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
````

Publons API documentation: <https://publons.com/api/v2/>

Use your regular Publons credentials to access the API. Signup for Publons at <https://publons.com/account/signup/>.

Find your institution name here:
<https://publons.com/institution/?order_by=num_reviewers>
