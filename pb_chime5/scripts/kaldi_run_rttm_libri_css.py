"""

python -m pb_chime5.scripts.kaldi_run_rttm with storage_dir=<...> database_rttm=<...> [activity_rttm=<...>] session_id=dev job_id=1 number_of_jobs=1

"""

from pathlib import Path
import inspect

import sacred
from sacred.commands import print_config
from sacred.observers import FileStorageObserver

import dlp_mpi

from pb_chime5.core_chime6_rttm import get_enhancer

experiment = sacred.Experiment('Chime5 Array Enhancement')


@experiment.config
def config():
    locals().update({k: v.default for k, v in inspect.signature(get_enhancer).parameters.items()})

    session_id = 'dev'
    storage_dir: str = None
    database_rttm: str = None
    activity_rttm: str = database_rttm

    job_id = 1
    number_of_jobs = 1

    assert storage_dir is not None, (storage_dir, 'overwrite the storage_dir from the command line')
    assert database_rttm is not None, (database_rttm, 'overwrite the database_rttm from the command line')
    assert activity_rttm is not None, (database_rttm, 'overwrite the activity_rttm from the command line')

    if dlp_mpi.IS_MASTER:
        experiment.observers.append(FileStorageObserver.create(str(
            Path(storage_dir).expanduser().resolve() / 'sacred'
        )))

@experiment.named_config
def my_test_rttm():
    database_rttm = '/scratch/hpc-prf-nt1/cbj/net/vol/boeddeker/chime6/kaldi/egs/chime6/s5_track2_download/data/dev_beamformit_dereverb_stats_seg/rttm.U06'


get_enhancer = experiment.capture(get_enhancer)


@experiment.main
def main(_run, storage_dir):
    run(_run, storage_dir=storage_dir)


@experiment.command
def test_run(_run, storage_dir, test_run=True):
    assert test_run is not False, test_run
    run(_run, storage_dir=storage_dir, test_run=test_run)


@experiment.capture
def run(_run, storage_dir, job_id, number_of_jobs, session_id, test_run=False):
    print_config(_run)

    assert job_id >= 1 and job_id <= number_of_jobs, (job_id, number_of_jobs)

    enhancer = get_enhancer()

    if test_run:
        print('Database', enhancer.db)

    if test_run is False:
        dataset_slice = slice(job_id - 1, None, number_of_jobs)
    else:
        dataset_slice = test_run

    if dlp_mpi.IS_MASTER:
        print('Enhancer:', enhancer)
        print(session_id)

    enhancer.enhance_session(
        session_id,
        Path(storage_dir) / 'audio',
        dataset_slice=dataset_slice,
        audio_dir_exist_ok=True,
    )

    if dlp_mpi.IS_MASTER:
        print('Finished experiment dir:', storage_dir)


if __name__ == '__main__':
    experiment.run_commandline()
