import os
import re

import fetch.fetch_utils as fetch_utils
import asyncio
import aiohttp


async def fetch(identifier, session: aiohttp.ClientSession):
    # full_url = URL + identifier
    base_url = "https://annas-archive.org/scidb/"
    async with session.get(url=base_url + identifier) as res:
        pdf_url = fetch_utils.find_pdf_url(await res.text())

    # print(f"full url: {full_url}")
    if pdf_url:
        async with session.get(url=pdf_url) as res:
            return await res.read()
    else:
        return None


doi_regexes = [
    r"10.\d{4,9}\/[-._;()\/:A-Z0-9]+",
    r"10.1002\/[^\s]+",
    r"10.\d{4}\/\d+-\d+X?(\d+)\d+<[\d\w]+:[\d\w]*>\d+.\d+.\w+;\d",
    r"10.1021\/\w\w\d++",
    r"10.1207/[\w\d]+\&\d+_\d+",
]


# TODO: deduplicate with parse.parse_ids_from_text
# this is only here because of importing errors
def parse_doi_from_text(s: str) -> list[dict[str, str]]:
    seen = set()
    matches = []
    for regex in doi_regexes:
        for match in re.findall(regex, s, re.IGNORECASE):
            if match not in seen:
                matches.append({"id": match, "type": "doi"})
            seen.add(match)
    return matches


async def save_scidb(
    session: aiohttp.ClientSession,
    identifier,
    out,
    name=None,
):
    # scidb only accepts DOI
    is_doi = parse_doi_from_text(identifier)
    # TODO: add exception handling
    if is_doi:
        result = await fetch(
            identifier,
            session,
        )
        path = os.path.join(out, fetch_utils.generate_name(result))
        if result:
            with open(path, "wb") as f:
                f.write(result)
            new_path = fetch_utils.rename(out, path, name)
            return new_path
    raise Exception(f"identifer {identifier} source not found")
