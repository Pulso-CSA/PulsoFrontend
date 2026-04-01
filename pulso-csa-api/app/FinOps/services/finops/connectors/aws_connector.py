#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮AWS Connector – boto3 + Cost Explorer❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from datetime import datetime, timedelta
from typing import Any, Optional

from services.finops.connectors.base import BaseCloudConnector


class AWSConnector(BaseCloudConnector):
    """Conector AWS: Cost Explorer, EC2, EBS, S3, CloudWatch (quando disponível)."""

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        session_token: Optional[str] = None,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> None:
        self._access_key = access_key_id
        self._secret_key = secret_access_key
        self._session_token = session_token
        self._role_arn = role_arn
        self._external_id = external_id
        self._region = region or "us-east-1"
        self._session = None

    def _get_session(self):
        """Obtém sessão boto3 (AssumeRole ou credenciais diretas)."""
        if self._session is not None:
            return self._session
        try:
            import boto3
            from botocore.config import Config
            config = Config(
                connect_timeout=self.REQUEST_TIMEOUT,
                read_timeout=self.REQUEST_TIMEOUT,
                retries={"max_attempts": 2, "mode": "standard"},
            )
            if self._role_arn:
                sts = boto3.client(
                    "sts",
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    aws_session_token=self._session_token,
                    config=config,
                )
                assume_params = {"RoleArn": self._role_arn, "RoleSessionName": "FinOpsAnalyze"}
                if self._external_id:
                    assume_params["ExternalId"] = self._external_id
                creds = sts.assume_role(**assume_params)["Credentials"]
                self._session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                )
            else:
                self._session = boto3.Session(
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    aws_session_token=self._session_token,
                    region_name=self._region,
                )
            return self._session
        except ImportError:
            raise RuntimeError("boto3 não instalado. Execute: pip install boto3")

    def preflight(self) -> tuple[bool, str]:
        """Valida credenciais via STS GetCallerIdentity."""
        try:
            sess = self._get_session()
            sts = sess.client("sts")
            sts.get_caller_identity()
            return True, "Credenciais válidas"
        except Exception as e:
            return False, f"AWS preflight falhou: {type(e).__name__}: {str(e)[:200]}"

    def collect_billing(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Cost Explorer: custo por serviço e total."""
        sess = self._get_session()
        ce = sess.client("ce", region_name="us-east-1")
        start = start_date or (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        end = end_date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            result = ce.get_cost_and_usage(
                TimePeriod={"Start": start, "End": end},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
            total = 0.0
            by_service: list[dict] = []
            for rb in result.get("ResultsByTime", []):
                for g in rb.get("Groups", []):
                    amount = float(g.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0))
                    total += amount
                    by_service.append({"service": g.get("Keys", ["Unknown"])[0], "amount_usd": amount})
            return {
                "total_cost_usd": round(total, 2),
                "period": {"start": start, "end": end},
                "by_service": by_service[:30],
            }
        except Exception as e:
            return {"error": str(e)[:200], "total_cost_usd": None}

    def collect_inventory(self) -> dict[str, Any]:
        """Inventário resumido: EC2, EBS, S3, etc."""
        sess = self._get_session()
        region = self._region
        inventory: dict[str, Any] = {"ec2": [], "ebs": [], "s3_buckets": 0, "lambda_count": 0}
        try:
            ec2 = sess.client("ec2", region_name=region)
            instances = ec2.describe_instances()
            for r in instances.get("Reservations", []):
                for i in r.get("Instances", []):
                    inventory["ec2"].append({
                        "id": i.get("InstanceId"),
                        "type": i.get("InstanceType"),
                        "state": i.get("State", {}).get("Name"),
                        "region": region,
                    })
            inventory["ec2"] = inventory["ec2"][:50]
        except Exception:
            inventory["ec2_error"] = "Não foi possível listar EC2"
        try:
            s3 = sess.client("s3")
            buckets = s3.list_buckets()
            inventory["s3_buckets"] = len(buckets.get("Buckets", []))
        except Exception:
            inventory["s3_error"] = "Não foi possível listar S3"
        return inventory

    def collect_metrics(self) -> dict[str, Any]:
        """CloudWatch: CPU quando disponível (por instância específica)."""
        sess = self._get_session()
        try:
            ec2 = sess.client("ec2", region_name=self._region)
            reservations = ec2.describe_instances()
            instance_ids = []
            for r in reservations.get("Reservations", []):
                for i in r.get("Instances", []):
                    if i.get("State", {}).get("Name") == "running":
                        instance_ids.append(i["InstanceId"])
                        break
                if instance_ids:
                    break
            if not instance_ids:
                return {"avg_cpu_utilization": None, "note": "Nenhuma instância running para métricas"}
            cw = sess.client("cloudwatch", region_name=self._region)
            now = datetime.utcnow()
            start = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
            end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            resp = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_ids[0]}],
                StartTime=start,
                EndTime=end,
                Period=86400,
                Statistics=["Average"],
            )
            points = resp.get("Datapoints", [])
            avg_cpu = sum(p.get("Average", 0) for p in points) / len(points) if points else 0
            return {"avg_cpu_utilization": round(avg_cpu, 2), "datapoints": len(points)}
        except Exception:
            return {"avg_cpu_utilization": None, "note": "CloudWatch não disponível"}

    def _provider_name(self) -> str:
        return "aws"
