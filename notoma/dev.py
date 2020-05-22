from pathlib import Path
from typing import Union
import click
import nbformat
from nbconvert.exporters import MarkdownExporter
from nbconvert.preprocessors import RegexRemovePreprocessor


ROOT_PATH = Path(__file__).parent.parent
NBS_PATH = ROOT_PATH / "notebooks/"
DOCS_PATH = ROOT_PATH / "docs/"


@click.group(help="Notoma dev tools: tests and documentation generators.")
def cli():
    """
    The CLI group method wrapped in @click.group
    to invoke the dev commands.
    """
    pass


@cli.command(help="Generate documentation pages in `docs` from `notebooks`.")
def docs():
    nbs = [f for f in NBS_PATH.glob("*.ipynb")]

    for fname in nbs:
        fname = Path(fname).absolute()
        dest = Path(f"{DOCS_PATH/fname.stem}.md").absolute()
        print(f"Converting {fname} to {dest}")
        _convert_nb_to_md(fname, dest)

    _make_readme(NBS_PATH / "index.ipynb")


def _get_metadata(notebook: list) -> dict:
    if not notebook["cells"]:
        raise ValueError("Expected the input to be NotebookCell-like list")

    md_cells = [c["source"] for c in notebook["cells"] if c["cell_type"] == "markdown"]
    meta = {"layout": "default"}

    for cell in md_cells:
        if cell.startswith("%METADATA%"):
            for line in cell.split("\n")[1:]:
                k, v, *rest = [part.strip() for part in line.split(":")]
                meta[k.lower()] = v
    return meta


def _convert_nb_to_md(
    fname: Union[str, Path], dest: Union[str, Path] = DOCS_PATH
) -> None:
    """
    Converts a Jupyter Notebook in `fname` to a Jekyll-compatible Markdown file
    including front matter metadata for Just The Docs.
    """
    notebook = nbformat.read(str(fname), as_version=4)
    metadata = _get_metadata(notebook)
    exporter = _build_exporter()

    prep = RegexRemovePreprocessor()
    prep.patterns = [r"![\s\S]", "^%METADATA%", "^#hide"]
    notebook, _ = prep.preprocess(notebook, {})

    converted = exporter.from_notebook_node(notebook, resources={"meta": metadata})
    with open(str(dest), "w") as f:
        f.write(converted[0])


def _build_exporter() -> MarkdownExporter:
    """
    Build a MarkdownExporter with a custom template
    and return it.
    """
    exporter = MarkdownExporter()
    exporter.template_file = "docs-jekyll.md.j2"
    exporter.template_path.append(str(Path(__file__).parent / "templates"))
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    return exporter


def _make_readme(fname: Union[str, Path]):
    """
    Converts a notebook at `fname` to README.md in repository root.
    """
    _convert_nb_to_md(fname, ROOT_PATH / "README.md")
