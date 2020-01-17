"""
A set of processes to generate/process fastq/fasta files
"""
from os import path
from diot import Diot
from . import params, proc_factory

# pylint: disable=invalid-name

pFastq2Expr = proc_factory(
    desc='Call gene expression from pair-end fastq files using kallisto.',
    config=Diot(annotate="""
    @input:
        fqfile1: The fastq file1.
        fqfile2: The fastq file2.
    @output:
        outfile: The expression file
        outdir : Output direcotry with expression and other output files
    @args:
        params   (Diot) : Other parameters for `kallisto quant`.
        idxfile  (path): The kallisto index file.
        kallisto (path): The path to `kallisto`.
        nthread  (int) : # threads to use.
    """,
                runcmd_pre="""
        {{"reference.bash" | bashimport}}
        reference kallisto {{args.idxfile | quote}}
    """),
    lang=params.python.value,
    input='fqfile1:file, fqfile2:file',
    output=[
        '''outfile:file:{{ i.fqfile1, i.fqfile2 | commonprefix
                                                | .rstrip: "._[]"
                        }}.kallisto/{{i.fqfile1, i.fqfile2 | commonprefix
                                                           | .rstrip: "._[]"
                                                           | bn }}.expr.txt''',
        '''outdir:dir:{{ i.fqfile1, i.fqfile2 | commonprefix
                                                | .rstrip: "._[]" }}.kallisto'''
    ],
    args=Diot(
        kallisto=params.kallisto.value,
        params=Diot(),
        nthread=1,
        idxfile=params.kallistoIdx.value,
    )
)

pFastqSim = proc_factory(
    desc='Simulation of pair-end reads',
    config=Diot(annotate="""
    @input:
        `seed`: The seed to generate simulation file
            - None: use current timestamp.
    @output:
        fq1: The first pair read file
        fq2: The second pair read file
    @args:
        tool (str) : The tool used for simulation. Could be one of:
            - wgsim/dwgsim/art_illumina
        len1         (int) : The length of first pair read.
        len2         (int) : The length of second pair read.
        num          (int) : The number of read PAIRs.
        gz           (bool): Whether generate gzipped read file.
        wgsim        (path): The path of wgsim.
        dwgsim       (path): The path of wgsim.
        art_illumina (path): The path of art_illumina.
        ref          (path): The reference genome. Required
        params       (Diot) : Other params for the tool
    @requires:
        [wgsim](https://github.com/lh3/wgsim)
        [dwgsim](https://github.com/nh13/DWGSIM)
        [art](https://www.niehs.nih.gov/research/resources/software/biostatistics/art/): `conda install -c bioconda art`
    """),
    lang=params.python.value,
    input='seed',
    output=[
        'fq1:file:read_seed{{i.seed}}_1.fq{{args.gz | ? | =:".gz" | !:""}}',
        'fq2:file:read_seed{{i.seed}}_2.fq{{args.gz | ? | =:".gz" | !:""}}'
    ],
    args=Diot(
        tool='dwgsim',
        wgsim=params.wgsim.value,
        dwgsim=params.dwgsim.value,
        art_illumina=params.art_illumina.value,
        len1=150,
        len2=150,
        num=1000000,
        gz=False,
        params=Diot(),
        ref=params.ref.value,
    )
)

pFastQC = proc_factory(
    desc='QC report for fastq file.',
    config=Diot(annotate="""
    @name:
        pFastQC
    @description:
        QC report for fastq file
    @input:
        `fq:file`:    The fastq file (also fine with gzipped)
    @output:
        `outdir:dir`: The output direcotry
    @args:
        `tool`:    The tool used for simulation. Default: fastqc
        `fastqc`:  The path of fastqc. Default: fastqc
        `nthread`: Number of threads to use. Default: 1
        `params`:Other params for `tool`. Default: ""
    @requires:
        [`fastqc`](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/)
    """),
    input="fq:file",
    output="""outdir:dir:{{i.fq | stem | ?.endswith: '.gz' | =:_[:-3]
                                | $?.endswith: '.fastq' | =:_[:-6]
                                | $?.endswith: '.fq' | =:_[:-3]
                                | $?.endswith: '.clean' | =:_[:-6]
                                | $?.endswith: '_clean' | =:_[:-6]}}.fastqc""",
    lang=params.python.value,
    args=Diot(
        tool='fastqc',
        fastqc=params.fastqc.value,
        nthread=1,
        params=Diot(),
    )
)

pFastMC = proc_factory(
    desc='Multi-QC based on pFastQC.',
    config=Diot(annotate="""
    @name:
        pFastMC
    @description:
        Multi-QC based on pFastQC
    @input:
        `qcdir:file`:  The direcotry containing QC files
    @output:
        `outdir:dir`: The output direcotry
    @args:
        `tool`:    The tool used for simulation. Default: multiqc
        `multiqc`: The path of fastqc. Default: multiqc
        `params`:  Other params for `tool`. Default: ""
    @requires:
        [`multiqc`](http://multiqc.info/)
    """),
    input="qcdir:file",
    output="outdir:dir:{{i.qcdir | fn}}.multiqc",
    lang=params.python.value,
    args=Diot(
        tool='multiqc',
        multiqc=params.multiqc.value,
        params=Diot(),
    )
)

pFastqTrim = proc_factory(
    desc='Trim pair-end reads in fastq file.',
    config=Diot(annotate="""
    @input:
        fq1: The input fastq file 1
        fq2: The input fastq file 2
    @output:
        outfq1: The trimmed fastq file 1
        outfq2: The trimmed fastq file 2
    @args:
        tool       : The tools used for trimming. Available: trimmomatic, cutadapt or skewer
        cutadapt   : The path of seqtk.
        skewer     : The path of fastx toolkit trimmer.
        trimmomatic: The path of trimmomatic.
        params     : Other params for `tool`.
        nthread    : Number of threads to be used.
            - Not for cutadapt
        gz : Whether gzip output files.
        mem: The memory to be used.
            - Only for trimmomatic
        minlen: Discard trimmed reads that are shorter than `minlen`.
            - For trimmomatic, the number will be `minlen`*2 for MINLEN, as it filters before trimming
        minq: Minimal mean qulity for 4-base window or leading/tailing reads.
        cut5: Remove the 5'end reads if they are below qulity.
        cut3: Remove the 3'end reads if they are below qulity.
            - Not for skewer
        adapter1: The adapter for sequence.
        adapter2: The adapter for pair-end sequence.
    @requires:
        [`cutadapt`](http://cutadapt.readthedocs.io/en/stable/guide.html)
        [`skewer`](https://github.com/relipmoc/skewer)
        [`trimmomatic`](https://github.com/timflutre/trimmomatic)
    """),
    lang=params.python.value,
    input="fq1:file, fq2:file",
    output=[
        """outfq1:file:{{i.fq1 | stem | ?.endswith: '.gz' | =:_[:-3]
                               | $?.endswith: '.fastq' | =:_[:-6]
                               | $?.endswith: '.fq' | =:_[:-3]
                               | $?.endswith: '.clean' | =:_[:-6]
                               | $?.endswith: '_clean' | =:_[:-6]
                       }}.fastq{{args.gz | ? | =:".gz" | !:""}}""",
        """outfq2:file:{{i.fq2 | stem | ?.endswith: '.gz' | =:_[:-3]
                               | $?.endswith: '.fastq' | =:_[:-6]
                               | $?.endswith: '.fq' | =:_[:-3]
                               | $?.endswith: '.clean' | =:_[:-6]
                               | $?.endswith: '_clean' | =:_[:-6]
                       }}.fastq{{args.gz | ? | =:".gz" | !:""}}"""
    ],
    args=Diot(tool='skewer',
              cutadapt=params.cutadapt.value,
              skewer=params.skewer.value,
              trimmomatic=params.trimmomatic.value,
              params=Diot(),
              nthread=1,
              gz=False,
              mem=params.mem4G.value,
              minlen=18,
              minq=3,
              cut5=3,
              cut3=3,
              adapter1='AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC',
              adapter2='AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTA')
)

pFastqSETrim = proc_factory(
    desc='Trim single-end reads in fastq file.',
    config=Diot(annotate="""
    @name:
        pFastqSETrim
    @description:
        Trim single-end FASTQ reads
    @input:
        `fq:file`:  The input fastq file
    @output:
        `outfq:file`: The trimmed fastq file
    @args:
        `tool`        : The tools used for trimming. Default: trimmomatic (cutadapt|skewer)
        `cutadapt`    : The path of seqtk. Default: cutadapt
        `skewer`      : The path of fastx toolkit trimmer. Default: skewer
        `trimmomatic` : The path of trimmomatic. Default: trimmomatic
        `params`      : Other params for `tool`. Default: ""
        `nthread`     : Number of threads to be used. Default: 1
            - Not for cutadapt
        `gz`          : Whether gzip output files. Default: True
        `mem`         : The memory to be used. Default: 4G
            - Only for trimmomatic
        `minlen`      : Discard trimmed reads that are shorter than `minlen`. Default: 18
            - For trimmomatic, the number will be `minlen`*2 for MINLEN, as it filters before trimming
        `minq`        : Minimal mean qulity for 4-base window or leading/tailing reads. Default: 3
        `cut5`        : Remove the 5'end reads if they are below qulity. Default: 3
        `cut3`        : Remove the 3'end reads if they are below qulity. Default: 3
            - Not for skewer
        `adapter`     : The adapter for sequence. Default: AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC
    @requires:
        [`cutadapt`](http://cutadapt.readthedocs.io/en/stable/guide.html)
        [`skewer`](https://github.com/relipmoc/skewer)
        [`trimmomatic`](https://github.com/timflutre/trimmomatic)
    """),
    input="fq:file",
    output="""outfq:file:{{i.fq | stem | ?.endswith: '.gz' | =:_[:-3]
                                | $?.endswith: '.fastq' | =:_[:-6]
                                | $?.endswith: '.fq' | =:_[:-3]
                                | $?.endswith: '.clean' | =:_[:-6]
                                | $?.endswith: '_clean' | =:_[:-6]
                         }}.fastq{{args.gz | ? | =:".gz" | !:""}}""",
    lang=params.python.value,
    args=Diot(
        tool='skewer',
        cutadapt=params.cutadapt.value,
        skewer=params.skewer.value,
        trimmomatic=params.trimmomatic.value,
        params=Diot(),
        nthread=1,
        gz=False,
        mem=params.mem4G.value,
        minlen=18,
        minq=3,
        cut5=3,
        cut3=3,
        adapter='AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC',
    )
)

pFastqSE2Sam = proc_factory(
    desc='Map cleaned single-end fastq file to reference genome.',
    config=Diot(annotate="""
    @name:
        pFastqSE2Sam
    @description:
        Cleaned paired fastq (.fq, .fq.gz, .fastq, .fastq.gz file to mapped sam/bam file
    @args:
        `tool`:   The tool used for alignment. Default: bwa (bowtie2|ngm)
        `bwa`:    Path of bwa, default: bwa
        `ngm`:    Path of ngm, default: ngm
        `bowtie2`:Path of bowtie2, default: bowtie2
        `rg`:     The read group. Default: {'id': '', 'pl': 'Illumina', 'pu': 'unit1', 'lb': 'lib1', 'sm': ''}
            - `id` will be parsed from filename with "_LX_" in it if not given
            - `sm` will be parsed from filename
        `ref`:    Path of reference file
        `params`: Other params for tool, default: ''
    """),
    input="fq:file",
    output="""outfile:file:{{i.fq | stem | ?.endswith: '.gz' | =:_[:-3]
                                  | $?.endswith: '.fastq' | =:_[:-6]
                                  | $?.endswith: '.fq' | =:_[:-3]
                                  | $?.endswith: '.clean' | =:_[:-6]
                                  | $?.endswith: '_clean' | =:_[:-6]
                           }}.{{args.outfmt}}""",
    lang=params.python.value,
    args=Diot(
        outfmt="sam",
        tool='bwa',
        bwa=params.bwa.value,
        ngm=params.ngm.value,
        star=params.star.value,
        samtools=params.samtools.value,
        bowtie2=params.bowtie2.value,
        bowtie2_build=params.bowtie2.value + '-build',
        rg=Diot(id='', pl='Illumina', pu='unit1', lb='lib1', sm=''),
        ref=params.ref.value,
        refgene=params.refgene.value,
        nthread=1,
        params=Diot(),
    )
)

pFastq2Sam = proc_factory(
    desc='Map cleaned paired fastq file to reference genome.',
    config=Diot(
        annotate="""
        @description:
            Cleaned paired fastq (.fq, .fq.gz, .fastq, .fastq.gz file to mapped sam/bam file
        @args:
            `tool`   : The tool used for alignment. Available: bowtie2, ngm or star.
            `bwa`    : Path of bwa
            `ngm`    : Path of ngm
            `star`   : Path of STAR
                - The genomeDir should be at `/path/to/hg19.star` if `args.ref` is `/path/to/hg19.fa`
            `bowtie2`: Path of bowtie2
            `rg`:     The read group.
                - `id` will be parsed from filename with "_LX_" in it if not given
                - `sm` will be parsed from filename
            `ref`    : Path of reference file
            `refexon`: The GTF file for STAR to build index. It's not neccessary if index is already been built.
            `params` : Other params for tool
        """,
        runcmd_pre="""
            {{"reference.bash" | bashimport}}
            export bwa={{args.bwa | squote}}
            export ngm={{args.ngm | squote}}
            export star={{args.star | squote}}
            export samtools={{args.samtools | squote}}
            export bowtie2={{args.bowtie2 | squote}}
            export nthread={{args.nthread}}
            export refexon={{args.refexon | squote}}
            reference {{args.tool | squote}} {{args.ref | squote}}
        """
    ),
    lang=params.python.value,
    input="fq1:file, fq2:file",
    output="""outfile:file:{{i.fq1, i.fq2 | commonprefix
                                          | .rstrip: '_. ,[]'
                           }}.{{args.outfmt}}""",
    envs=Diot(path=path),
    args=Diot(tool='bwa',
              outfmt='sam',
              bwa=params.bwa.value,
              ngm=params.ngm.value,
              star=params.star.value,
              samtools=params.samtools.value,
              bowtie2=params.bowtie2.value,
              rg=Diot(id='', pl='Illumina', pu='unit1', lb='lib1', sm=''),
              ref=params.ref.value,
              refexon=params.refexon.value,
              nthread=1,
              params=Diot())
)
