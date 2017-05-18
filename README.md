# aws-audit
AWS Audit Scripts - CloudFront subdomain takeover audit, etc

# Checks all cloudfront domain registrations and route53 DNS records for specified AWS profiles to see if any at risk
./cloudfront-subdomain-audit.py --profiles 'dev,stage,prod'
