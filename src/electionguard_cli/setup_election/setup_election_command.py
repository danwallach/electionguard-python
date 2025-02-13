from io import TextIOWrapper
import click

from .output_setup_files_step import OutputSetupFilesStep
from ..cli_steps import KeyCeremonyStep, ElectionBuilderStep
from .setup_input_retrieval_step import SetupInputRetrievalStep


@click.command("setup")
@click.option(
    "--guardian-count",
    prompt="Number of guardians",
    help="The number of guardians that will participate in the key ceremony and tally.",
    type=click.INT,
)
@click.option(
    "--quorum",
    prompt="Quorum",
    help="The minimum number of guardians required to show up to the tally.",
    type=click.INT,
)
@click.option(
    "--manifest",
    prompt="Manifest file",
    help="The location of an election manifest.",
    type=click.File(),
)
@click.option(
    "--out",
    prompt="Output directory",
    help="The location of a directory into which will be placed the output files such as "
    + "context, constants, and guardian keys. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def SetupElectionCommand(
    guardian_count: int, quorum: int, manifest: TextIOWrapper, out: str
) -> None:
    """
    This command runs an automated key ceremony and produces the files
    necessary to encrypt ballots, decrypt an election, and produce an election record.
    """

    election_inputs = SetupInputRetrievalStep().get_inputs(
        guardian_count, quorum, manifest, out
    )
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs.guardians)
    build_election_results = ElectionBuilderStep().build_election_with_key(
        election_inputs, joint_key
    )
    OutputSetupFilesStep().output(election_inputs, build_election_results)
