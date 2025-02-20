# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2025 TUBITAK ULAKBIM.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI for Invenio internationalization module"""
import click
import json
from importlib.metadata import entry_points
from pathlib import Path

from flask.cli import with_appcontext


@click.group(chain=True)
@with_appcontext
def i18n():
    """i18n commands."""


@i18n.command()
@with_appcontext
@click.option('-i', '--input-directory',
              required=True,
              type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=False, path_type=Path),
              help='Input directory containing translations in JSON format.')
def distribute_js_translations(input_directory):
    """Distribute JavaScript translations"""
    EXCEPTIONAL_PACKAGE_NAME_MAPPER = {
        "jobs": "invenio-jobs",
        "invenio-previewer-theme": "invenio-previewer",
        "invenio-app-rdm-theme": "invenio-app-rdm"
    }
    bundle_entrypoints = [ep for ep in entry_points(group="invenio_assets.webpack")]

    PACKAGE_TRANSLATIONS_BASE_PATHS = {}
    for bundle_entrypoint in bundle_entrypoints:
        package_name = bundle_entrypoint.name.replace("_", "-")
        bundle = bundle_entrypoint.load()
        if bundle.path:
            if package_name in EXCEPTIONAL_PACKAGE_NAME_MAPPER:
                package_name = EXCEPTIONAL_PACKAGE_NAME_MAPPER[package_name]
            PACKAGE_TRANSLATIONS_BASE_PATHS[package_name] = Path(bundle.path) / "translations"

    # Get combined translation files by languages
    source_translation_files = {}
    for path in input_directory.iterdir():
        if path.is_file() and path.suffix == ".json":
            source_translation_files[path.stem] = path

    for lang in source_translation_files:
        with open(source_translation_files[lang], 'r') as source_translations_file:
            combined_translations = source_translations_file.read()
            combined_translations = json.loads(combined_translations)
            for package in combined_translations:
                if package in PACKAGE_TRANSLATIONS_BASE_PATHS:
                    module = package.replace("-", "_")
                    target_translations_path = PACKAGE_TRANSLATIONS_BASE_PATHS[package] / module / "messages" / lang
                    if not Path(target_translations_path).exists():
                        click.secho(
                            f"Translation directory for {lang} not found in {PACKAGE_TRANSLATIONS_BASE_PATHS[package] / module / "messages"}. Creating...",
                            fg="yellow")
                        Path(target_translations_path).mkdir()

                    target_translations_file_path = Path(target_translations_path) / "translations.json"
                    with open(target_translations_file_path, "w+") as target_translations_file:
                        try:
                            target_translations_file.write(
                                json.dumps(combined_translations[package], indent=2, ensure_ascii=False))
                            click.secho(f"Translations for {package} in {lang} have been written.", fg="green")
                        except Exception as e:
                            raise e

                else:
                    click.secho(f"{package} doesn't have webpack entrypoint. Skipping...", fg="yellow", italic=True)
