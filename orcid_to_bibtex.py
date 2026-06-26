#!/usr/bin/env python3

import requests
import re
import argparse
import pathlib

# Regular Expression used to recognize an ORCID
ORCID_RE = re.compile(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]')


def check_orcid(orcid):
    if not re.fullmatch(ORCID_RE, orcid):
        raise ValueError('The provided string is not a valid ORCID identifier')
    return orcid


def read_work(work_summary):
    path = work_summary['path']
    resp = requests.get('https://pub.orcid.org' + path,
                        headers={'Accept': 'application/orcid+json'})
    data = resp.json()
    return data


def read_publications(orcid):
    check_orcid(orcid)
    resp = requests.get('https://pub.orcid.org/' + orcid,
                        headers={'Accept': 'application/orcid+json'})
    data = resp.json()
    works = data['activities-summary']['works']['group']
    result = []
    for work in works:
        summaries = work['work-summary']
        # ORCID groups duplicate entries from multiple sources under one work.
        # The first summary is the preferred/primary source per ORCID API docs.
        if summaries:
            result.append(read_work(summaries[0]))
    return result


def pub_key(pub):
    pub_year = None
    pub_month = 12
    put_code = int(pub['put-code'])
    if 'publication-date' in pub:
        sub = pub['publication-date']
        try:
            pub_year = int(sub['year']['value'])
        except:
            pass
        try:
            pub_month = int(sub['month']['value'])
        except:
            pass
    return (pub_year, pub_month, put_code)


def generate_bibtex(publications):
    sorted_pubs = sorted(publications, key=pub_key, reverse=True)
    bibtex_citations = [pub['citation']['citation-value'].strip() for pub in sorted_pubs if pub.get('citation')]
    print(f'Found {len(bibtex_citations)} citations for the bibliography')
    return '\n\n'.join(bibtex_citations)


def main():
    parser = argparse.ArgumentParser(description='Generate BibTeX file from ORCID profile.')
    parser.add_argument('-o', '--output', type=pathlib.Path,
                        default='bibliography.bib', help="Output file to write the BibTeX data to")
    parser.add_argument('ORCID', type=check_orcid,
                        help='And ORCID. This should be 4 groups of 4 digits separated by hyphens (the last digit can also be X)')
    args = parser.parse_args()
    data = read_publications(args.ORCID)
    with open(args.output, 'w', encoding='utf-8') as out:
        out.write(generate_bibtex(data))


if __name__ == '__main__':
    main()