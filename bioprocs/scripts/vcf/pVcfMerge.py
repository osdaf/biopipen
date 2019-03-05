from pyppl import Box
from bioprocs.utils import shell
from bioprocs.utils.parallel import Parallel
from bioprocs.utils.reference import vcfIndex

invcfs    = {{i.infiles | repr}}
outfile   = {{o.outfile | quote}}
nthread   = {{args.nthread | int}}
joboutdir = {{job.outdir | quote}}
vcftools  = {{args.vcftools | quote}}
bcftools  = {{args.bcftools | quote}}
gatk      = {{args.gatk | quote}}
tabix     = {{args.tabix | quote}}
ref       = {{args.ref | quote}}
params    = {{args.params | repr}}
tool      = {{args.tool | quote}}
gz        = {{args.gz | repr}}

shell.TOOLS.bcftools = bcftools
shell.TOOLS.vcftools = vcftools
shell.TOOLS.gatk     = gatk

para = Parallel(nthread, raiseExc = True)
invcfs = para.run(vcfIndex, [
	(vcf, tabix) for vcf in invcfs
])
# don't reuse it
del para


def run_vcftools():
	params.d       = params.get('d', True)
	params.t       = params.get('t', True)
	params.R       = params.get('R', '0/0')
	params._       = invcfs
	params._stdout = outfile[:-3] if gz else outfile
	shell.Shell(equal = ' ').vcftools(**params).run()
	if gz: shell.bgzip(outfile[:-3])

def run_bcftools():
	params.F       = params.get('F', '+')
	params.o       = outfile
	params.threads = nthread
	params._       = invcfs
	params['0']    = params.get('0', True)
	if gz:
		params.O = 'z'
	shell.Shell(subcmd = True, equal = ' ').bcftools.merge(**params).run()

def run_gatk():
	params.T                   = 'CombineVariants'
	params.o                   = outfile
	params.R                   = ref
	params.nt                  = nthread
	params.variant             = invcfs
	params._stdout             = outfile[:-3] if gz else outfile
	params.genotypemergeoption = params.get('genotypemergeoption', 'UNIQUIFY')
	shell.Shell(equal = ' ', duplistkeys = True).gatk(**params).run()
	if gz: shell.bgzip(outfile[:-3])

tools = dict(
	vcftools = run_vcftools,
	bcftools = run_bcftools,
	gatk     = run_gatk,
)

try:
	tools[tool]()
except KeyError:
	raise KeyError('Tool {!r} not supported.'.format(tool))
except:
	raise
finally:
	pass