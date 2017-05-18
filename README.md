# aws-audit
AWS Audit Scripts - CloudFront subdomain takeover audit, etc

# Checks all cloudfront domain registrations and route53 DNS records for specified AWS profiles to see if any at risk
./cloudfront-subdomain-audit.py --profiles 'dev,stage,prod'

    ```
    /cloudfront-subdomain-audit.py --profiles 'dev,stage,prod'
    Retrieving CloudFront data from AWS profile: dev
    Retrieving CloudFront data from AWS profile: stage
    Retrieving CloudFront data from AWS profile: prod
    Auditing dev records
    Auditing stage records
    Auditing prod records
    RISK: api.mikelikebike.com: alias: api2.mikelikebike.com not in our CF Distros
    ```
