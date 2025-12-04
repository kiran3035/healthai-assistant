#!/usr/bin/env python3
"""
AWS Resource Cleanup Script
----------------------------
Deletes all AWS resources created by the HealthAI Assistant CloudFormation stack
to avoid ongoing costs. Run this after you're done testing.

Usage:
    python scripts/cleanup_aws.py --stack-name healthai-stack

Requirements:
    - AWS CLI configured with appropriate credentials
    - boto3 installed (pip install boto3)
"""

import argparse
import time
import sys

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("ERROR: boto3 is required. Install it with: pip install boto3")
    sys.exit(1)


def delete_cloudformation_stack(stack_name: str, region: str) -> bool:
    """
    Delete CloudFormation stack and wait for completion.
    This will delete EC2, IAM roles, Security Groups automatically.
    """
    cf_client = boto3.client("cloudformation", region_name=region)
    
    print(f"\n🗑️  Deleting CloudFormation stack: {stack_name}")
    print("   This will delete: EC2 instance, IAM roles, Security Groups")
    
    try:
        cf_client.delete_stack(StackName=stack_name)
        print("   Stack deletion initiated...")
        
        # Wait for deletion
        waiter = cf_client.get_waiter("stack_delete_complete")
        print("   Waiting for deletion to complete (this may take a few minutes)...")
        waiter.wait(StackName=stack_name)
        print("   ✅ Stack deleted successfully!")
        return True
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ValidationError" and "does not exist" in str(e):
            print(f"   ⚠️  Stack '{stack_name}' does not exist or already deleted.")
            return True
        print(f"   ❌ Error deleting stack: {e}")
        return False


def delete_opensearch_collection(collection_name: str, region: str) -> bool:
    """
    Delete OpenSearch Serverless collection.
    Note: CloudFormation should handle this, but this is a backup.
    """
    try:
        aoss_client = boto3.client("opensearchserverless", region_name=region)
        
        print(f"\n🗑️  Checking OpenSearch collection: {collection_name}")
        
        # Check if collection exists
        try:
            response = aoss_client.batch_get_collection(names=[collection_name])
            if not response.get("collectionDetails"):
                print("   ⚠️  Collection does not exist or already deleted.")
                return True
        except ClientError:
            print("   ⚠️  Collection not found.")
            return True
        
        # Delete collection
        aoss_client.delete_collection(id=response["collectionDetails"][0]["id"])
        print("   ✅ Collection deletion initiated!")
        
        # Wait for deletion
        print("   Waiting for collection deletion...")
        for _ in range(30):  # Wait up to 5 minutes
            time.sleep(10)
            try:
                response = aoss_client.batch_get_collection(names=[collection_name])
                if not response.get("collectionDetails"):
                    print("   ✅ Collection deleted successfully!")
                    return True
            except ClientError:
                print("   ✅ Collection deleted successfully!")
                return True
        
        print("   ⚠️  Collection deletion is taking longer than expected. Check AWS Console.")
        return False
        
    except ClientError as e:
        print(f"   ❌ Error: {e}")
        return False


def delete_security_policies(region: str) -> None:
    """Delete OpenSearch Serverless security policies."""
    try:
        aoss_client = boto3.client("opensearchserverless", region_name=region)
        
        print("\n🗑️  Cleaning up OpenSearch security policies...")
        
        # Delete encryption policy
        try:
            aoss_client.delete_security_policy(name="healthai-encryption", type="encryption")
            print("   ✅ Deleted encryption policy")
        except ClientError:
            print("   ⚠️  Encryption policy not found or already deleted")
        
        # Delete network policy
        try:
            aoss_client.delete_security_policy(name="healthai-network", type="network")
            print("   ✅ Deleted network policy")
        except ClientError:
            print("   ⚠️  Network policy not found or already deleted")
            
    except Exception as e:
        print(f"   ⚠️  Could not clean up policies: {e}")


def estimate_cost_savings():
    """Print estimated cost savings."""
    print("\n💰 Estimated Cost Savings:")
    print("   • EC2 t3.medium: ~$30/month")
    print("   • OpenSearch Serverless: ~$24/month (minimum)")
    print("   • Data transfer: Variable")
    print("   • Total: ~$54+/month saved")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up AWS resources created by HealthAI Assistant"
    )
    parser.add_argument(
        "--stack-name",
        default="healthai-stack",
        help="CloudFormation stack name (default: healthai-stack)"
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--skip-confirmation",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("    HealthAI Assistant - AWS Resource Cleanup")
    print("=" * 60)
    print(f"\n📍 Region: {args.region}")
    print(f"📦 Stack: {args.stack_name}")
    
    if not args.skip_confirmation:
        print("\n⚠️  WARNING: This will permanently delete all resources!")
        confirm = input("\nType 'yes' to confirm deletion: ")
        if confirm.lower() != "yes":
            print("\n❌ Cleanup cancelled.")
            sys.exit(0)
    
    # Delete CloudFormation stack (handles most resources)
    stack_deleted = delete_cloudformation_stack(args.stack_name, args.region)
    
    # Clean up OpenSearch collection (backup if CF fails)
    delete_opensearch_collection("healthai-knowledge", args.region)
    
    # Clean up security policies
    delete_security_policies(args.region)
    
    # Summary
    print("\n" + "=" * 60)
    if stack_deleted:
        print("✅ Cleanup completed successfully!")
        estimate_cost_savings()
    else:
        print("⚠️  Cleanup completed with some issues. Check AWS Console.")
    print("=" * 60)


if __name__ == "__main__":
    main()
