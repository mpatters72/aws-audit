# aws-audit
* Scripts to audit AWS accounts
## cloudfront-subdomain-audit.py
    Find Route53 records pointing to CloudFront and whether or not all CF Aliases are registered
    Note: All aliases in chain are found by DNS resolution and Cloudfront status checked by CIDR block
    Option to provide list of aws profiles from ~/.aws/credentials if desired
    https://labs.detectify.com/2014/10/21/hostile-subdomain-takeover-using-herokugithubdesk-more/

### Example usage
./cloudfront-subdomain-audit.py --profiles 'dev,stage,prod'

```
Retrieving CloudFront data from AWS profile: dev
Retrieving CloudFront data from AWS profile: stage
Retrieving CloudFront data from AWS profile: prod
Auditing dev records
Auditing stage records
Auditing prod records
RISK: api.mikelikebike.com: alias: api2.mikelikebike.com not in our CF Distros
```
# s3 Scripts
## Scripts for modifying/auditing s3 policies, versioning, and lifecycle rules

### s3ListPublic.py
* List buckets with public ACLs or policies applied to s3 bucket
* --pattern can match to s3 bucket names, or skip argument to look at all buckets
* Usage:
    ```
    ./s3ListPublic.py --pattern <matchingstring in bucketname>

    ./s3ListPublic.py
    mikey-mikepatterson-test Read - AllUsers Access: List Objects
    mikey-mikepatterson-test * has : s3:GetObject
    ```

### s3Tag.py
* Adds/updates tags for s3 buckets that match name
* Assumes aws profile is set in ~/.aws/credentials
* Caveat works great as long as your bucket doesn't have any tags starting with 'aws', like the ones created by cloudformation
* s3 instances created by Cloudformation can be updated by creating a changeset, validating only tags changed, and applying change
* Related discussion [https://github.com/capitalone/cloud-custodian/issues/370]
* only required argument is 'pattern'
* if --addtags 'no', it'll just show info w/o updating
* Usage:
    ```
    s3Tag.py --pattern [matchingstring in bucketname] --addtags <yes|no> --tagkey <keyname> --tagvalue <keyvalue>
    ```
* List Tags, Add and Update Tag examples
    ```
    ./s3Tag.py --pattern 'mikepatterson'
    mikey-mikepatterson-test NO TAGS

    ./s3Tag.py --pattern 'mikepatterson' --addtags 'yes' --tagkey 'testkey' --tagvalue 'testvalue'
    mikey-mikepatterson-test NO TAGS
    Planning to add/update this tag: testkey value: testvalue to the matching buckets shown
    ########## status after update ##########
    mikey-mikepatterson-test testkey testvalue

### s3EnableVersioning.py
* While it's preferable to create s3 buckets and set policy in Cloudformation, these are used to audit update outside of that process
* Enables versioning and sets number of days to keep old versions of files at whole bucket level
* For build deployments, we override the "HEAD" file.  Probably a good idea to be able to roll-back to previous version if needed in emergency
* Applying LifeCycle policies is risky as it applied at an all or nothing way.  So there it counts existing rules and will fail if existing policies are already on bucket.
* Assumes aws profile is set in ~/.aws/credentials
* Usage:
    ```
    s3EnableVersioning.py --bucket [bucketname] --days [days]
    s3EnableVersioning.py --bucket 'mikey-mikepatterson-test' --days 90
    ```

