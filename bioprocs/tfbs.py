from pyppl import Proc, Box
#from .utils import runcmd, helpers, parallel
from . import params
from .utils import fs2name

"""
@name:
	pMotifScan
@description:
	Scan motif along the given sequences.
@input:
	`tffile:file`: The infile containing TF name and motif name.
		- If only one column is give, will be used as both TF and motif name
		- If there are 2+ columns, 1st column will be motif name, 2nd column will be TF name
	`sfile:file`: The sequence file
@output:
	`outdir:file`: The output dir
@args:
	`tools`   : The tool used to scan the motif. Default: 'meme'
	`meme`    : The path of MEME's fimo. Default: 'fimo'
	`motifs`  : The motif database in MEME format.
	`pval`    : The pvalue cutoff. Default: 1e-4
	`cleanmname`: Whether to clean motif name. Default: True
	`ucsclink`: The ucsc link template. Default: `https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position={}`
	`nthread` : Number of threads used to scan, only available when you have multiple mids. Default: 1
	`params`  : Other parameters for `fimo`
@requires:
	[`fimo` from MEME Suite](http://meme-suite.org/tools/fimo)
"""
pMotifScan                        = Proc(desc = 'Scan motif along the given sequences.')
pMotifScan.input                  = "tffile:file, sfile:file"
pMotifScan.output                 = [
	"outfile:file:{{i.sfile | fn}}-{{i.tffile | fn}}.fimo/{{i.sfile | fn}}-{{i.tffile | fn}}.bed", 
	"outdir:dir:{{i.sfile | fn}}-{{i.tffile | fn}}.fimo"
]
pMotifScan.args.tool     = 'meme'
pMotifScan.args.meme     = params.fimo.value
pMotifScan.args.params   = Box()
pMotifScan.args.tfmotifs = params.tfmotifs.value
pMotifScan.args.pval     = 1e-4
pMotifScan.args.ucsclink = 'https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position={}'
pMotifScan.args.nthread  = 1
pMotifScan.lang          = params.python.value
pMotifScan.script        = "file:scripts/tfbs/pMotifScan.py"

pMotifSimilarity        = Proc(desc = 'Compare the similarity between motifs.')
pMotifSimilarity.input  = 'mfile1:file, mfile2:file'
pMotifSimilarity.output = [
	'outfile:file:{{i.mfile1, i.mfile2, args.tool, fn2, path.join | *&odfn | *:e(f, c+".txt") }}',
	'outdir:dir:{{i.mfile1, i.mfile2, args.tool, fn2 | *odfn }}'
]
pMotifSimilarity.args.tool   = 'tomtom'
pMotifSimilarity.args.qval   = 0.5
pMotifSimilarity.args.tomtom = params.tomtom.value
pMotifSimilarity.args.params = Box({
	'xalph': True, 'no-ssc': True, 'dist': 'pearson', 'min-overlap': 1, 'motif-pseudo': .1, 'verbosity': 4
})
pMotifSimilarity.args.nthread = 1
pMotifSimilarity.envs.path    = __import__('os').path
pMotifSimilarity.envs.odfn    = lambda f1, f2, tool, fn2, p = None: (fn2(f1) + "-" + fn2(f2) if f2 else fn2(f1)) + "." + tool
pMotifSimilarity.lang         = params.python.value
pMotifSimilarity.script       = "file:scripts/tfbs/pMotifSimilarity.py"

pMotifMerge              = Proc(desc = 'Merge motif files in MEME format')
pMotifMerge.input        = 'infiles:files'
pMotifMerge.output       = 'outfile:file:{{i.infiles | fs2name}}.meme.txt'
pMotifMerge.envs.fs2name = fs2name
pMotifMerge.lang         = params.python.value
pMotifMerge.script       = "file:scripts/tfbs/pMotifMerge.py"

pMotifFilter             = Proc(desc = 'Filter motifs from a meme file.')
pMotifFilter.input       = 'infile:file'
pMotifFilter.output      = 'outfile:file:{{i.infile | bn}}'
pMotifFilter.args.filter = None
pMotifFilter.lang        = params.python.value
pMotifFilter.script      = "file:scripts/tfbs/pMotifFilter.py"

"""
@name:
	pAtSnp
@description:
	Scan motifs on Snps to detect binding affinity changes.
@input:
	`tffile:file`:  The tf-motif file with 1st column the motif and 2nd the tf
	`snpfile:file`: The snp file. 
		- Could be a bed file with first 6 columns the bed6 format and 7th the reference allele, and 8th the alternative alleles.
		- Alleles including reference allele should be seperated by `,`
		- It also could be a snp file required by `atSNP` package.
		- See: https://rdrr.io/github/kinsigne/atSNP_modified/man/LoadSNPData.html
@output:
	`outfile:file`: The output file
	`outdir:dir`  : The output directory containing the output file and plots.
@args:
	`tfmotifs`: The motif database. Defaut: `params.tfmotifs`
	`genome`  : The reference genome to get the sequences. Default: `params.genome`
	`fdr`     : Do fdr or not. Or could be the p-value adjustment method. Default: `True` (using `BH` method)
	`pval`    : The pvalue cutoff for output and plot.
	`plot`    : Do plot or not. Default: `True`
	`nthread` : How many threads to use. Default: `1`
	`depvars` : The device parameters for plotting. Default: `Box(res = 300, width = 2000, height = 2000)`
@requires:
	`r-atSNP`
"""
pAtSnp               = Proc(desc = 'Scan motifs on Snps to detect binding affinity changes.')
pAtSnp.input         = 'tffile:file, snpfile:file'
pAtSnp.output        = [
	'outfile:file:{{i.tffile | fn2}}-{{i.snpfile | fn2}}.atsnp/{{i.tffile | fn2}}-{{i.snpfile | fn2}}.atsnp.txt',
	'outdir:dir:{{i.tffile | fn2}}-{{i.snpfile | fn2}}.atsnp'
]
pAtSnp.args.tfmotifs = params.tfmotifs.value
pAtSnp.args.genome   = params.genome.value
pAtSnp.args.fdr      = True
pAtSnp.args.pval     = 0.05
pAtSnp.args.plot     = True
pAtSnp.args.nthread  = 1
pAtSnp.args.devpars  = Box(res = 300, width = 2000, height = 2000)
pAtSnp.lang          = params.Rscript.value
pAtSnp.script        = "file:scripts/tfbs/pAtSnp.r"

