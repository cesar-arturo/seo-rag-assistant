import pytest

from seo_rag.spark import get_spark


@pytest.mark.integration
def test_serverless_connection():
    spark = get_spark()
    assert spark.sql("SELECT 1 AS ok").collect()[0].ok == 1
