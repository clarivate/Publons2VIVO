## Publons2VIVO
### Summary
Publons2VIVO is a script that queries the Publons API and produces VIVO-compatible linked data. The API can be queried via either Publons IDs and ORCIDs or by organization name. The script attempts to match the person results (via Publons ID or ORCID) and journals (via ISSN or EISSN) to objects already in your VIVO instance.

### Installation
1. Run `pip install -r requirements.txt` to install dependencies. 
2. Set required environment variables, e.g.
```
$ export PUBLONS_USER='publons-user@school.edu'
$ export PUBLONS_PASSWORD='password'
$ export DATA_NAMESPACE='http://vivo.school.edu/individual/'
$ export VIVO_URL='http://localhost:8080/vivo'
$ export VIVO_EMAIL='vivo_root@school.edu'
$ export VIVO_PASSWORD='rootPassword'
```
### Usage

```
$ python publons2vivo.py --help
usage: publons2vivo.py [-h] (-o ORGANIZATION | -i IDS) [--api] [-a]
                       [-f {xml,n3,turtle,nt,pretty-xml,trix}] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  -o ORGANIZATION, --organization ORGANIZATION
                        Pull data for all researchers affiliated with this
                        organization.
  -i IDS, --ids IDS     The ORCID or Publons ID to search
  --api                 Send the newly created triples to VIVO using the
                        update API. Note, there is no undo button! You have
                        been warned!
  -f {xml,n3,turtle,nt,pretty-xml,trix}, --format {xml,n3,turtle,nt,pretty-xml,trix}
                        The RDF format for serializing. Default is turtle.
  --debug               Set logging level to DEBUG.

```
```
$ python publons2vivo.py --ids "243325,523116,1285537,1177532"
2018-06-07 06:46:40,681 - [INFO] - Wrote RDF to rdf/publons-2018-06-07 06:46:40-in.ttl in turtle format.

$ python publons2vivo.py --organization "Washington University, Saint Louis"
2018-06-07 07:00:15,121 - [INFO] - Wrote RDF to rdf/publons-2018-06-07 07:00:15-in.ttl in turtle format.
```

Publons API documentation: <https://publons.com/api/v2/>

Use your regular Publons credentials to access the API. Sign up for Publons at <https://publons.com/account/signup/>.

Find your institution name here:
<https://publons.com/institution/?order_by=num_reviewers>
