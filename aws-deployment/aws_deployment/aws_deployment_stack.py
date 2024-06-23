from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_iam as iam
)
from constructs import Construct

class AwsDeploymentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        site_bucket = s3.Bucket(self, "rsschool-task2-s3",
                                bucket_name="rsschool-task2-spa-vm622-bucket",
                                website_index_document="index.html",
                                removal_policy=RemovalPolicy.DESTROY,
                                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                auto_delete_objects=True)
        
        oai = cloudfront.OriginAccessIdentity(self, "my_oai", comment="OAI for CloudFront")

        distribution = cloudfront.Distribution(self, "MyCloudfrontDistribution-rsschool-task2", 
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(site_bucket, origin_access_identity=oai), 
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            default_root_object="index.html")
        

        site_bucket.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[site_bucket.arn_for_objects("*")],
            principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
            conditions={
                "StringEquals": {
                    "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
                }                     
            }
        ))

        site_bucket.grant_read(oai)

        s3deploy.BucketDeployment(self, "DeployWithInvalidation",
                                sources=[s3deploy.Source.asset(("../dist"))],
                                destination_bucket=site_bucket,
                                distribution=distribution,
                                distribution_paths=["/*"])
