# ACAI Cache-Query Documentation <a id="top">
<!-- LOGO -->
<a href="https://acai.gmbh">
    <img src="https://acai.gmbh/images/logo/logo-acai-badge.png" alt="acai logo" title="acai" align="right" width="100" />
</a>

<!-- SHIELDS -->
[![Maintained by acai.gmbh][acai-shield]][acai-url] ![Copyright by acai.gmbh][acai-copyright-shield]

This is the documentation of the ACAI JSON-Engine.

# Content

- [Object In Scope](#object_in_scope)
- [Short JSON Intro](#json_intro)
- [ACAI JSON-Engine](#acai_json_engine)
  - [Syntax Examples](#acai_json_engine_examples)
    - [Source JSON](#acai_json_engine_examples_source)
    - [Pattern JSON](#acai_json_engine_examples_patterns)
      - [AND / OR](#acai_json_engine_examples_and_or)
      - [Comparator "exists"](#acai_json_engine_examples_exists)
      - [Comparator "regex-*"](#acai_json_engine_examples_regex)

## Object In Scope <a id="object_in_scope"></a> [🔝](#top)

Often you have a bundle of JSON-Objects you want to treat similarly.
An example would be all AWS Accounts in an AWS Organization. The context of an AWS Account would consist of an AccountID, -name and -tags and the AWS Organization Unit (OU) information, outlined in the following JSON-Object:

```python
cache_query = {
      "accountId": "123456789012",
      "accountName": "aws-core-provisioning",
      "accountTags": {
        "account_email": "accounts+aws-c1-provisioning@acai.gmbh",
        "account_name": "aws-c1-provisioning",
        "account_owner": "semper_rocks@acai.gmbh",
        "environment": "nonprod",
        "tenant": "acai",
        "tfc_execution_mode": "remote",
        "title": "provisioning account - customer1 stage"
      },
      "ouId": "ou-1234-12345678",
      "ouName": "Branding",
      "ouNameWithPath": "/Branding"
    }
```

In our example, all AWS Accounts of an AWS Organization would be in scope by default.
Now let's assume, you want to select all non-prod accounts from specific Organization Units (e.g. /DMZ).

For this use case, we have introduced a **Scope Pattern JSON**.
![JSON-Engine-Scope-Pattern-Image]

It first allows you to specify an optional exclude block. The JSON-Value can either be **"*"**, which excludes all default objects or a **Pattern JSON-Object** or a list of **Pattern JSON-Objects** specifying a bundle of JSON-Objects to exclude.

```text
<Scope Pattern JSON-Key>: Scope Pattern JSON-Object
or
<Scope Pattern JSON-Key>: [Scope Pattern JSON-Object, Scope Pattern JSON-Object]

with <Scope Pattern JSON-Object> = {
    "exclude": "*" | Pattern JSON-Object | [
        Pattern JSON-Object
    ],
    "forceInclude": Pattern JSON Object | [
        Pattern JSON Object
    ]
}
```

| Key           | Value-Type                                                 | Comment    |
| :---          | :---                                                       | :---       |
| .exclude      | "*" or Pattern JSON-Object or List of Pattern JSON-Objects | (optional) |
| .forceInclude | Pattern JSON-Object or List of Pattern JSON-Objects        | (optional) |

**Object in Scope Example #1**

```json {linenos=table,hl_lines=[],linenostart=50}
query_json =  {
    "exclude": "*",
    "forceInclude": {
        "accountName": [
            {
                "contains": "-core-"
            }
        ]
    }
}
```

```text
-> Scope Pattern JSON will select all AWS Accounts where "accountContext"."accountName" contains "-core-"
```

**Object in Scope Example #2**

```json {linenos=table,hl_lines=[],linenostart=50}
query_json = {
    "exclude": "*",
    "forceInclude": [
        {
            "accountTags": {
                "environment": "nonprod"
            },
            "ouNameWithPath": [
                {
                    "contains": "department_a_"
                }
            ]
        }
    ]
}
```

```text
-> Scope Pattern JSON will select all AWS Accounts where 
   "accountContext"."accountTags"."environment" equals "nonprod" and   
   "accountContext"."ouNameWithPath" contains "department_a_"
```

**Object in Scope Example #3**

```json {linenos=table,hl_lines=[],linenostart=50}
query_json = {
    "exclude": "*",
    "forceInclude": [
        {
            "accountTags": {
                "environment": "nonprod"
            }
        },
        {
            "ouNameWithPath": [
                {
                    "contains": "sandbox"
                }
            ]
        }
    ]
}
```

```text
-> Scope Pattern JSON will select all AWS Accounts where 
   "accountContext"."accountTags"."environment" equals "nonprod" or 
   "accountContext"."ouNameWithPath" contains "sandbox"
```

**Object in Scope Example #4**

```json {linenos=table,hl_lines=[],linenostart=50}
query_json = {
    "exclude": {
        "accountTags": {
            "environment": "core"
        }
    }
}
```

```text
-> Scope Pattern JSON will select all AWS Accounts that are not 
   "accountContext"."accountTags"."environment" equals "core"
```

**Object in Scope Example #5**

```json {linenos=table,hl_lines=[],linenostart=50}
query_json = [
    {
        "exclude": "*",
        "forceInclude": {
            "ouNameWithPath": [
                {
                    "contains": "dept_2"
                }
            ]
        }
    },
    {
        "exclude": "*",
        "forceInclude": {
            "accountTags": {
                "environment": "prod"
            },
            "ouNameWithPath": [
                {
                    "contains": "dept_1"
                }
            ]
        }
    }
]
```

```text
-> Scope Pattern JSON will select all AWS Accounts where
   "accountContext"."ouNameWithPath" contains "dept_2" or where 
   "accountContext"."accountTags"."environment" equals "prod" and 
   "accountContext"."ouNameWithPath" contains "dept_1"
```

# Short JSON Intro <a id="json_intro"></a> [🔝](#top)

A JSON-Object can be seen as a key-value store, able to describe complex models.
The following diagram gives an overview of the most important JSON terms inspired by [www.json.org](https://www.json.org/json-en.html).

![JSON-Basics-Image]

# ACAI JSON-Engine <a id="acai_json_engine"></a> [🔝](#top)

The principle of the ACAI JSON-Engine is based on the comparison of a **Pattern JSON** with a **Source JSON**.
![JSON-Engine-Image]

The syntax of the **Pattern JSON** is in alignment with [Amazon EventBridge > Create event patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html#eb-create-pattern):

| Comparison | Example | Rule syntax | Matching source example |
| :---   | :---  | :---  | :---  |
| Equals | Name is "Alice" | "Name": "Alice" or "Name": [ "Alice" ]  | "Name": "Alice" |
| And | Location is "New York" and Day is "Monday" | "Location": "New York", <br/>"Day": "Monday" | "Location": "New York",<br/> "Day": "Monday" |
| Or | PaymentType is "Credit" | "Debit" | "PaymentType": [ "Credit", "Debit"] | "PaymentType": "Credit" |
| Empty | LastName is empty | "LastName": [""] | "LastName": "" |
| "Nesting" | Customer.Name is "Alice" | "Customer": JSON Object | "Customer": { "Name": "Alice" }  |
| Mix | Location is "New York" and Day is "Monday" or "Tuesday" | "Location": "New York", <br/> "Day": ["Monday", "Thuesday"] | "Location": "New York", "Day": "Monday" or <br/> "Location": "New York", "Day": "Tuesday" |

## Logical Expressions <a id="acai_json_engine_logical_expressions"></a> [🔝](#top)

Additional **Logical Expressions** are supported. In this case, the JSON-Value is a JSON-Array of JSON-Objects:

<img src="docs/Logical-Expression.svg" alt="drawing" width="400"/>

```Note
**Note**
For the ACAI JSON-Engine the keys of the Pattern JSON are case-insensitive to the Source JSON. 
```

| Comparison | Comparator | Example | Logical Expression Syntax | Matching Source JSON |
| :---   | :---  |  :---  | :---  | :---  |
| Begins with | prefix | Region is in the US | "Region": [ {"prefix": "us-" } ] | "Region": "us-east-1" |
| Contains | contains | ServiceName contains 'database' | "ServiceName": [ <br/>  {"contains": "database" } <br/>] |  "serviceName": "employee-database-dev" |
| Does not contain | contains-not | ServiceName does not contain 'database' | "ServiceName": [ <br/>  {"contains-not": "database" } <br/>] |  "serviceName": "employee-microservice-dev" |
| Ends with | suffix | Service name ends with "-dev" | "serviceName": [ {"suffix": "-dev" } ] | "ServiceName": "employee-database-dev" |
| Not | anything-but | Weather is anything but "Raining" | "Weather": [<br/>  { "anything-but": "Raining" } <br/>] | "Weather": "Sunny" or "Cloudy" |
| Exists | exists | ProductName exists | "ProductName": [ { "exists": true } ] | "ProductName": "SEMPER" |
| Does not exist | exists | ProductName does not exist | "ProductName": [ { "exists": false } ] | n/a |
| REGEX match | regex-match | ServiceName matches regex pattern "^prefix-\w+-prod$" |  "ServiceName": [<br/>  { "regex-match": "^prefix-\w+-prod$" } <br/>] |  "ServiceName": "prefix-database-prod" |
| REGEX not match | regex-not-match | ServiceName does not match regex pattern "^prefix-\w+-prod$" |  "ServiceName": [<br/>  { "regex-match": "^prefix-\w+-prod$" } <br/>] |  "ServiceName": "prefix-database-int" |

## Syntax Examples <a id="acai_json_engine_examples"></a> [🔝](#top)

### Source JSON  <a id="acai_json_engine_examples_source"></a> [🔝](#top)

```json {linenos=table,hl_lines=[],linenostart=50}
{
    "sourceIPAddress": "87.200.73.179",
    "requestParameters": {
        "ipPermissions": {
            "items": [
                {
                    "ipProtocol": "tcp",
                    "fromPort": 70,
                    "toPort": 90,
                    "ipRanges": {
                        "items": [
                            {
                                "cidrIp": "0.0.0.0/16"
                            }
                        ]
                    }
                }
            ]
        }
    },
    "readOnly": false,
    "eventType": "AwsApiCall",
    "managementEvent": true,
    "recipientAccountId": "123456789012",
    "eventCategory": "Management",
    "sessionCredentialFromConsole": "true",
    "a-count": 5,
    "b-count": 5,
    "c-count": 0,
    "d-count": 10,
    "x-limit": 3.5
}
```

### Pattern JSON <a id="acai_json_engine_examples_patterns"></a> [🔝](#top)

#### AND / OR <a id="acai_json_engine_examples_and_or"></a> [🔝](#top)

```json {linenos=table,hl_lines=[],linenostart=50}
{
    "readOnly": false,
    "eventType": "AwsApiCall",
    "recipientAccountId": [
        "123456789012",
        "234567890123"
    ],
    "requestParameters": {
        "ipPermissions": {
            "items": {
                "ipProtocol": "tcp"
            }
        }
    }
}
```

```text
-> Pattern JSON will match to the Source JSON as all conditions are met.
```

#### Comparator "exists" <a id="acai_json_engine_examples_exists"></a> [🔝](#top)

This example will prevent a race-condition for events generated by the auto-remediation principal.

```json {linenos=table,hl_lines=[],linenostart=50}
{
    "userIdentity": {
        "sessionContext": {
            "sessionIssuer": {
                "userName" : [
                    {
                        "exists": false
                    },
                    {
                        "exists": true,
                        "anything-but": "foundation-auto-remediation-role"
                    }      
                ]
            }
        }
    }
}
```

```text
-> Pattern JSON will match to the Source JSON as 
   "userIdentity"."sessionContext"."sessionIssuer"."userName" does not exist in the Source JSON.
   If the node ..."userName" would exist the Pattern JSON would match if 
   the ..."userName" would not be "foundation-auto-remediation-role". 
```


#### Comparator "regex-*" <a id="acai_json_engine_examples_regex"></a> [🔝](#top)

For regex expressions we recommend: https://www.autoregex.xyz/

**"regex-match" Example #1**

```json {linenos=table,hl_lines=[],linenostart=50}
{
    "eventType": [{"regex-match": "^Aws"}]
}
```

```text
-> Pattern JSON will match to the Source JSON as the 
   "eventType": "AwsApiCall" matches the pattern.
```

**"regex-match" Example #2**

```json {linenos=table,hl_lines=[],linenostart=50}
{
    "eventType": [{"regex-match": "^Azure"}]
}
```

```text
-> Pattern JSON will not match to the Source JSON as the 
   "eventType": "AwsApiCall" does not match the pattern.
```

**"regex-not-match" Example #1**

```json {linenos=table,hl_lines=[],linenostart=50}
{
    "eventType": [{"regex-not-match": "^Aws"}]
}
```

```text
-> Pattern JSON will not match to the Source JSON as the 
   "eventType": "AwsApiCall" matches the pattern.
```

**"regex-not-match" Example #2**

```json {linenos=table,hl_lines=[],linenostart=50}
{
    "eventType": [{"regex-not-match": "^Azure"}]
}
```

```text
-> Pattern JSON will match to the Source JSON as the 
   "eventType": "AwsApiCall" does not match the pattern.
```


<!-- MARKDOWN LINKS & IMAGES -->
[acai-shield]: https://img.shields.io/badge/maintained_by-acai.gmbh-CB224B?style=flat
[acai-url]: https://acai.gmbh
[acai-copyright-shield]: https://img.shields.io/badge/copyright-acai.gmbh-CB224B?style=flat

[JSON-Basics-Image]: ./docs/JSON-Basics.svg
[JSON-Engine-Image]: ./docs/JSON-Engine.svg
[JSON-Engine-Scope-Pattern-Image]: ./docs/JSON-Engine-Scope-Pattern.svg
