# DNS Query To Ufile.io

**Rule ID:** 1cbbeaaf-3c8c-4e4c-9d72-49485b6a176b  
**Status:** test  
**Version:** 1.0.0  
**Owner:** 

## Description
Detects DNS queries to "ufile.io", which was seen abused by malware and threat actors as a method for data exfiltration

## Log Source
- Product: windows
- Category: dns_query
- Service: n/a

## Tags
- attack.exfiltration
- attack.t1567.002


## References
- https://thedfirreport.com/2021/12/13/diavol-ransomware/


## False Positives
- DNS queries for "ufile" are not malicious by nature necessarily. Investigate the source to determine the necessary actions to take
