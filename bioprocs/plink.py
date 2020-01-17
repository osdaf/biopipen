"""
Procs for plink 1.9
"""
from diot import Diot
from . import params, proc_factory
from .vcf import pVcf2Plink
from .tcgamaf import pGTMat2Plink

# pylint: disable=invalid-name
pPlinkFromVcf = pVcf2Plink.copy()
pPlinkFromGTMat = pGTMat2Plink.copy()

pPlinkStats = proc_factory(
    desc='Do basic statistics with plink 1.9',
    config=Diot(annotate="""
    @name:
        pPlinkStats
    """),
    input='indir:dir',
    output='outdir:dir:{{i.indir | fn}}.plinkStats',
    lang=params.Rscript.value,
    args=Diot(
        plink=params.plink.value,
        nthread=False,
        params=Diot({
            'hardy': True,
            'het': True,
            'freq': True,
            'missing': True,
            'check-sex': True,
        }),
        cutoff=Diot({
            'hardy.hwe': 1e-5,
            'hardy.mingt': None,
            'het': 3,
            'freq': 0.01,
            'missing.sample': .95,
            'missing.snp': .95,
        }),
        plot=Diot({
            'hardy.hwe': True,
            'hardy.mingt': True,
            'het': True,
            'freq': True,
            'missing.sample': True,
            'missing.snp': True,
        }),
        devpars=Diot(res=300, width=2000, height=2000)
    )
)

pPlinkSampleFilter = proc_factory(
    desc=('Do sample filtering or extraction using '
          '`--keep[-fam]` or `--remove[-fam]`'),
    config=Diot(annotate="""
    @name:
        pPlinkSampleFilter
    """),
    input='indir:dir, samfile:file',
    output='outdir:dir:{{i.indir | bn}}',
    lang=params.python.value,
    args=Diot(
        plink=params.plink.value,
        keep=True,
        samid='iid',  # both or fid,
        fam=False,
        params=Diot(),
        nthread=False,
    )
)

pPlinkMiss = proc_factory(
    desc='Find samples and snps with missing calls',
    config=Diot(annotate="""
    @name:
        pPlinkMiss
    @description:
        Find samples and snps with missing calls, calculate the call rates and plot them.
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
    @output:
        `outdir:dir`: The output directory. Default: `{{i.indir | fn}}.miss`
            - `.imiss`: The miss calls for samples
            - `.lmiss`: The miss calls for snps
            - `.samplecr.fail`: The samples fail sample call rate cutoff (`args.samplecr`)
            - `.snpcr.fail`: The SNPs fail snp call rate cutoff (`args.snpcr`)
    @args:
        `plink`: The path to plink.
        `samplecr`: The sample call rate cutoff. Default: `.95`
        `snpcr`: The SNP call rate cutoff. Default: `.95`
        `plot`: Whether plot the distribution of the call rates? Default: `True`
        `devpars`: The device parameters for the plot. Default: `Diot(res=300, width=2000, height=2000)`
    """),
    input='indir:dir',
    output='outdir:dir:{{i.indir | fn}}.miss',
    lang=params.Rscript.value,
    args=Diot(
        plink=params.plink.value,
        samplecr=.95,
        snpcr=.95,
        plot=True,
        devpars=Diot(res=300, width=2000, height=2000),
    )
)

pPlinkFreq = proc_factory(
    desc='Filter snps with minor allele frequency.',
    config=Diot(annotate="""
    @name:
        pPlinkFreq
    """),
    input='indir:dir',
    output='outdir:dir:{{i.indir | fn}}.freq',
    lang=params.python.value,
    args=Diot(
        plink=params.plink.value,
        cutoff=0.01,
        plot=True,
        devpars=Diot(res=300, width=2000, height=2000),
    )
)

pPlinkSexcheck = proc_factory(
    desc='Check inconsistency between sex denoted and from genotypes.',
    config=Diot(annotate="""
    @name:
        pPlinkSexcheck
    @description:
        Check inconsistency between sex denoted and from genotypes.
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
    @output:
        `outdir:dir`: The output directory. Default: `{{i.indir | fn}}.sexcheck`
            - `.sexcheck`: The orginal sex check report from `plink`
            - `.sex.fail`: The samples that fail sex check.
    @args:
        `plink`: The path to plink.
    """),
    input='indir:dir',
    output='outdir:dir:{{i.indir | fn}}.sexcheck',
    lang=params.Rscript.value,
    args=Diot(plink=params.plink.value)
)

pPlinkHet = proc_factory(
    desc='Calculate the heterozygosity of each sample',
    config=Diot(annotate="""
    @name:
        pPlinkHet
    @description:
        Calculate the heterozygosity of each sample.
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
    @output:
        `outdir:dir`: The output directory. Default: `{{i.indir | fn}}.het`
            - `.het`: The heterozygosity file generated by `plink`.
            - `.het.fail`: The samples fail sample heterozygosity cutoff (`args.cutoff`)
    @args:
        `plink`: The path to plink.
        `cutoff`: The sample heterozygosity cutoff. Default: `3` (mean-3SD ~ mean+3SD)
        `plot`: Whether plot the distribution of the heterozygosity? Default: `True`
        `devpars`: The device parameters for the plot. Default: `Diot(res=300, width=2000, height=2000)`
    """),
    input='indir:dir',
    output='outdir:dir:{{i.indir | fn}}.het',
    lang=params.Rscript.value,
    args=Diot(
        plink=params.plink.value,
        cutoff=3,
        plot=True,
        devpars=Diot(res=300, width=2000, height=2000),
    )
)

pPlinkHWE = proc_factory(
    desc="Hardy-Weinberg Equilibrium report and filtering.",
    config=Diot(annotate="""
    @name:
        pPlinkHWE
    @description:
        Hardy-Weinberg Equilibrium report and filtering.
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
    @output:
        `outdir:dir`: The output directory. Default: `{{i.indir | fn}}.hwe`
            - `.hwe`: The HWE report by `plink`
            - `.hardy.fail`: The SNPs fail HWE test
    @args:
        `plink`: The path to plink.
        `cutoff`: The HWE p-value cutoff. Default: `1e-5`
        `plot`: Whether plot the distribution of the HWE p-values? Default: `True`
        `devpars`: The device parameters for the plot. Default: `Diot(res=300, width=2000, height=2000)`
    """),
    input='indir:dir',
    output='outdir:dir:{{i.indir | fn}}.hwe',
    lang=params.Rscript.value,
    args=Diot(
        plink=params.plink.value,
        cutoff=1e-5,
        mingt=.05,
        plot=True,
        devpars=Diot(res=300, width=2000, height=2000),
    )
)

pPlinkIBD = proc_factory(
    desc="Estimate the identity by descent (IBD)",
    config=Diot(annotate="""
    @name:
        pPlinkIBD
    @description:
        Estimate the degree of recent shared ancestry individual pairs,
        the identity by descent (IBD)
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
    @output:
        `outdir:dir`: The output directory. Default: `{{i.indir | fn}}.ibd`
            - `.genome`: The original genome report from `plink`
            - `.ibd.png`: The heatmap of PI_HAT
    @args:
        `plink`: The path to plink.
        `indep`: To give a concrete example: the command above that specifies 50 5 0.2 would a) consider a window of 50 SNPs, b) calculate LD between each pair of SNPs in the window, b) remove one of a pair of SNPs if the LD is greater than 0.5, c) shift the window 5 SNPs forward and repeat the procedure.
        `pihat`: The PI_HAT cutoff. Default: 0.1875 (see: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5007749/)
        `plot` : Whether plot the PI_HAT heatmap? Default: `True`
        `devpars`: The device parameters for the plot. Default: `Diot(res=300, width=2200, height=1600)`
        `samid`: Sample ids on the heatmap. Default: `iid`
            - Could also be `fid` or `fid<sep>iid`, or an R function: `function(fid, iid)`
        `anno` : The annotation file for the samples. Names must match the ones that are transformed by `args.samid`. Default: `''`
    """),
    input='indir:dir',
    output='outdir:dir:{{i.indir | fn}}.ibd',
    lang=params.Rscript.value,
    args=Diot(
        plink=params.plink.value,
        highld=params.highld.value,
        samid='iid',  # fid or a function (fid, iid),
        indep=[50, 5, .2],
        # ref: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5007749/,
        pihat=0.1875,
        plot=True,
        anno='',
        seed=None,
        devpars=Diot(res=300, width=2000, height=2000),
    )
)

pPlinkRemove = proc_factory(
    desc="Remove failed samples and SNPs",
    config=Diot(annotate="""
    @name:
        pPlinkRemove
    @description:
        Remove failed samples and/or SNPs
        The samples/SNPs to be removed should be generated by one of:
        `pPlinkHet`, `pPlinkHWE`, `pPlinkIBD` or `pPlinkMiss`
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
        `pdir:dir` : The output directory from one of the processes listed in description
            - It could also be the `.fail` file generated by those processes
    @output:
        `outdir:dir`: The output directory containing the `.bed/.bim/.fam` after filtering.
    @args:
        `plink`: The path to plink.
    """),
    input='indir:dir, pdir:dir',
    output='outdir:dir:{{i.indir | fn}}',
    lang=params.Rscript.value,
    args=Diot(plink=params.plink.value)
)

pPlink2Vcf = proc_factory(
    desc="Convert plink binary files to VCF file.",
    config=Diot(annotate="""
    @name:
        pPlink2Vcf
    @description:
        Convert plink binaries into VCF file.
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
    @output:
        `outfile:file`: The output vcf file.
    @args:
        `plink`: The path to plink.
        `gz`   : Whether bgzip the output vcf file. Default: `False`
        `samid`: What to use as sample ID. Default: `both`
            - `both`: use `<FID>_<IID>` as sample id
            - `fid` : use `<FID>` as sample id
            - `iid` : use `<IID>` as sample id
    """),
    input='indir:dir',
    output='outfile:file:{{i.indir | bn}}.vcf{% if args.gz %}.gz{% endif %}',
    lang=params.python.value,
    args=Diot(
        plink=params.plink.value,
        gz=False,
        samid='both',  # fid, iid,
        chroms={"23": "X", "24": "Y", "25": "XY", "26": "M"},
    )
)

pPlink2GTMat = proc_factory(
    desc="Convert plink binary files to genotype matrix",
    config=Diot(annotate="""
    @name:
        pPlink2GTMat
    @description:
        Convert plink binaries into genotype matrix.
    @input:
        `indir:dir`: The input directory containing .bed/.bim/.fam files
    @output:
        `outfile:file`: The output genotype matrix file.
    @args:
        `plink`: The path to plink.
        `samid`: What to use as sample ID. Default: `both`
            - `both`: use `<FID>_<IID>` as sample id
            - `fid` : use `<FID>` as sample id
            - `iid` : use `<IID>` as sample id
    """),
    input='indir:dir',
    output='outfile:file:{{i.indir | bn}}.gtmat.txt',
    lang=params.python.value,
    args=Diot(
        plink=params.plink.value,
        samid='both',  # fid, iid,
        addchr=True,
        snpid='{chr}_{pos}_{rs}_{ref}_{alt}',  # or raw,
        chroms={"23": "X", "24": "Y", "25": "XY", "26": "M"},
        nors="NOVEL",
    )
)

pPlinkPCA = proc_factory(
    desc="Perform PCA on genotype data and covariates.",
    config=Diot(annotate="""
    @name:
        pPlinkPCA
    @description:
        Do PCA on genotype data with PLINK
    @input:
        `indir`: The input directory with .bed/.bim/.fam files
    @output:
        `outfile:file`: The output file of selected PCs, Default: `{{i.indir | fn}}.plinkPCA/{{i.indir | fn}}.pcs.txt`
        `outdir:dir`: The output directory with output file and plots. Default: `{{i.indir | fn}}.plinkPCA`
    @args:
        `plink`: The path to `plink`, Default: `<params.plink>`
        `samid`: Which IDs to report in results, Default: `both`
            - `both`: Both family ID and individual ID connected with `_`
            - `iid`:  Individual ID
            - `fid`:  Family ID
        `nthread`: # threads to use, Default: `False`
            - `False`: Don't put `--threads` in plink command
        `indep`: `indep` used to prune LD SNPs. Default: `[50, 5, .2]`
        `highld`: High LD regions. Default: `<params.highld>`
        `params`: Other parameters for `plink --pca`. Default: `Diot(mind = .95)`
        `select`: Select first PCs in the output file. Default: `0.2`
            - `select < 1`: select PCs with contribution greater than `select`
            - `select >=1`: select first `select` PCs
        `plots` : Output plots. Default: `Diot(scree = Diot(ncp = 20))`
        `devpars`: The parameters for ploting device. Default: `Diot(height = 2000, width = 2000, res = 300)`
    """),
    lang=params.Rscript.value,
    input='indir:dir',
    output=[
        'outfile:file:{{i.indir | fn}}.plinkPCA/{{i.indir | fn}}.pcs.txt',
        'outdir:dir:{{i.indir | fn}}.plinkPCA'
    ],
    args=Diot(
        plink=params.plink.value,
        samid='both',  # fid, iid,
        nthread=False,
        indep=[50, 5, .2],  # used to prune LD SNPs,
        highld=params.highld.value,
        params=Diot(mind=.95),
        select=.2,
        plots=Diot(
            scree=Diot(ncp=20),
            # rownames of anno should be consistent with `args.samid`
            pairs=Diot(
                anno='',
                ncp=4,
                params=Diot(upper=Diot(continuous='density')),
                ggs=Diot(
                    theme={
                        "axis.text.x":
                            "r:ggplot2::element_text(angle = 60, hjust = 1)"
                    })
            ),
            # more to add
        ),
        devpars=Diot(height=2000, width=2000, res=300)
    )
)

pPlinkSimulate = proc_factory(
    desc="Simulate a set of SNPs",
    config=Diot(annotate="""
    @name:
        pPlinkSimulate
    """),
    input='seed',
    output='outdir:dir:simsnps.{{i.seed|?isinstance: int|!="noseed"}}.plink',
    lang=params.python.value,
    args=Diot(
        plink=params.plink.value,
        ncases=1000,
        nctrls=1000,
        nsnps=100,
        label='SNP',
        dprev=.01,
        minfreq=0,
        maxfreq=1,
        hetodds=1,
        homodds=1,
        params=Diot(),
    )
)
