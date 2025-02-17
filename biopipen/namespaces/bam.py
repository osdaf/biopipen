"""Tools to process sam/bam/cram files"""

from ..core.proc import Proc
from ..core.config import config


class CNVpytor(Proc):
    """Detect CNV using CNVpytor

    Input:
        bamfile: The bam file
        snpfile: The snp file

    Output:
        outdir: The output directory

    Envs:
        cnvpytor: Path to cnvpytor
        ncores: Number of cores to use (`-j` for cnvpytor)
        cases: Cases to run cnvpytor. A dictionary with keys as case names
            and values is also a dict
            - `chrom`: The chromosomes to run on
            - `binsizes`: The binsizes
            - `snp`: How to read snp data
            - `mask_snps`: Whether mask 1000 Genome snps
            - `baf_nomask`: Do not use P mask in BAF histograms

    """

    input = "bamfile:file, snpfile:file"
    output = "outdir:dir:{{in.bamfile | stem}}.cnvpytor"
    lang = config.lang.python
    envs = {
        "cnvpytor": config.exe.cnvpytor,
        "ncores": config.misc.ncores,
        "cases": {
            "Basic": {
                "chrom": [],
                "binsizes": [10000, 100000],
                # set False to disable snp data importing
                "snp": {
                    "sample": "",
                    "name1": [],
                    "ad": "AD",
                    "gt": "GT",
                    "noAD": False,
                },
                "mask_snps": True,
                "baf_nomask": False,
                # other arguments for -rd
            }
        },
    }
    script = "file://../scripts/bam/CNVpytor.py"
    plugin_opts = {"report": "file://../reports/bam/CNVpytor.svelte"}


class ControlFREEC(Proc):
    """Detect CNVs using Control-FREEC

    Input:
        bamfile: The bam file
        snpfile: The snp file

    Output:
        outdir: The output directory

    Envs:
        freec: Path to Control-FREEC executable
        ncores: Number of cores to use
        arggs: Other arguments for Control-FREEC

    """

    input = "bamfile:file, snpfile:file"
    output = "outdir:dir:{{in.bamfile | stem}}.freec"
    lang = config.lang.python
    envs = {
        "freec": config.exe.freec,
        "ncores": config.misc.ncores,
        "tabix": config.exe.tabix,
        "bedtools": config.exe.bedtools,
        "sambamba": config.exe.sambamba,
        "samtools": config.exe.samtools,
        # The "<ref>.fai" file will be used as chrLenFile
        "ref": config.ref.reffa,
        "refdir": config.ref.refdir,
        "rscript": config.lang.rscript,
        "binsize": 50_000,  # shortcut for args.general.window
        "args": {
            "general": {
                "ploidy": 2,
                "breakPointThreshold": 0.8,
            },
            "sample": {"mateOrientation": "FR"},
            "control": {},
            "BAF": {},
            "target": {},
        }
    }
    script = "file://../scripts/bam/ControlFREEC.py"
    plugin_opts = {"report": "file://../reports/bam/ControlFREEC.svelte"}
