import os

from pyspark.sql import SparkSession


def get_spark() -> SparkSession:
    """Return the cluster's Spark session on Databricks, or a serverless Databricks Connect session locally."""
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        return SparkSession.builder.getOrCreate()

    from databricks.connect import DatabricksSession

    return DatabricksSession.builder.serverless(True).getOrCreate()
