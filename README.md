# aws-audit
## cloudfront-subdomain-audit.py
    Find Route53 records pointing to CloudFront and whether or not all CF Aliases are registered
    Note: All aliases in chain are found by DNS resolution and Cloudfront status checked by CIDR block
    Option to provide list of aws profiles from ~/.aws/credentials if desired
    [additional info on subdomain takeover](https://labs.detectify.com/2014/10/21/hostile-subdomain-takeover-using-herokugithubdesk-more/)

### Example usage
./cloudfront-subdomain-audit.py --profiles 'dev,stage,prod'

    ```
    ./cloudfront-subdomain-audit.py --profiles 'dev,stage,prod'
    Retrieving CloudFront data from AWS profile: dev
    Retrieving CloudFront data from AWS profile: stage
    Retrieving CloudFront data from AWS profile: prod
    Auditing dev records
    Auditing stage records
    Auditing prod records
    RISK: api.mikelikebike.com: alias: api2.mikelikebike.com not in our CF Distros
    ```
