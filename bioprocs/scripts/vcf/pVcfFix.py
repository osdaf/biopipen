import gzip
from os import path
from cyvcf2 import VCF, Writer
from pyppl import Box
from bioprocs.utils import shell2 as shell

infile  = {{i.infile | quote}}
outfile = {{o.outfile | quote}}
# currently supported:
# clinvarLink  = True,
# addChr       = True,
# headerInfo   = {id1: {Number:1, Type:String, Description: xxx}},
# headerContig = {ref: xxx.fai/xxx.dict, notfound: drop}
# headerFormat = {id1: {Number:1, Type:String, Description: xxx}},
# headerFilter = {filter1: descirption1, filter2: desc2, ...}

fixes   = {{args.fixes | repr}}
ref     = {{args.ref | quote}}
reffai  = ref + '.fai'
refdict = ref[:-3] + '.dict'

def getContigsFromFai(fai):
	ret = {}
	with open(fai) as f:
		for line in f:
			parts = line.split('\t')
			ret[parts[0]] = int(parts[1])
	return ret

def getContigsFromDict(dictfile):
	ret = {}
	with open(dictfile) as f:
		for line in f:
			parts = line.split('\t')
			if parts[0] != '@SQ':
				continue
			ret[parts[1][3:]] = int(parts[2][3:])
	return ret

# fix clinvarLink first, because it will fail VCF parser
# just remove it
if fixes.clinvarLink or fixes.addChr:
	tmpoutfile = outfile + '.tmp'
	openfun = gzip.open if infile.endswith('.gz') else open
	with openfun(infile, 'rt', errors='replace') as fin, \
		openfun(tmpoutfile, 'wt', errors='replace') as fout:
		for line in fin:
			if line.startswith('#'):
				# if no header operated
				fout.write(line)
				continue
			parts = line.strip().split('\t')
			if fixes.addChr:
				parts[0] = parts[0] if parts[0].startswith('chr') else 'chr' + parts[0]
			info = parts[7]
			if fixes.clinvarLink:
				info = ';'.join(inf for inf in info.split(';') if not inf.startswith('<a href'))
			parts[7] = info

			fout.write('\t'.join(parts) + '\n')
	infile = tmpoutfile

pool = {}
if fixes.headerInfo not in (None, False):
	pool['info'] = set()
if fixes.headerContig not in (None, False):
	pool['contig'] = set()
if fixes.headerFormat not in (None, False):
	pool['format'] = set()
if fixes.headerFilter not in (None, False):
	pool['filter'] = set()

if pool:
	# scan the problems
	vcf  = VCF(infile)
	for variant in vcf:
		if fixes.headerContig not in (None, False):
			pool['contig'].add(variant.CHROM)
		if fixes.headerInfo not in (None, False):
			for key,_ in variant.INFO:
				pool['info'].add(key)
		if fixes.headerFormat not in (None, False):
			for key in variant.FORMAT:
				pool['format'].add(key)
		if fixes.headerFilter not in (None, False) and variant.FILTER:
			for filt in variant.FILTER.split(';'):
				pool['filter'].add(filt)
	vcf.close() # remove auto-generated headers

	if fixes.headerContig is True:
		fixes.headerContig = {}
	if fixes.headerInfo is True:
		fixes.headerInfo = {}
	if fixes.headerFormat is True:
		fixes.headerFormat = {}
	if fixes.headerFilter is True:
		fixes.headerFilter = {}

	vcf  = VCF(infile)
	for info_item in pool['info']:
		try:
			item_type = vcf[info_item]
			# auto added by cyvcf2
			if item_type['Description'] == '"Dummy"':
				raise KeyError()
		except KeyError:
			adict = fixes.headerInfo.get(info_item, {})
			adict = dict(
				ID          = info_item,
				Number      = adict.get('Number', 1),
				Type        = adict.get('Type', "String"),
				Description = adict.get('Description', info_item.upper())
			)
			vcf.add_info_to_header(adict)

	for fmt_item in pool['format']:
		try:
			item_type = vcf[fmt_item]
			if item_type['Description'] == '"Dummy"':
				raise KeyError()
		except KeyError:
			adict = fixes.headerFormat.get(fmt_item, {})
			adict = dict(
				ID          = fmt_item,
				Number      = adict.get('Number', 1),
				Type        = adict.get('Type', "String"),
				Description = adict.get('Description', fmt_item.upper())
			)
			vcf.add_format_to_header(adict)

	for filter_item in pool['filter']:
		try:
			item_type = vcf[filter_item]
		except KeyError:
			adict = fixes.headerFilter.get(filter_item, {})
			adict = dict(
				ID          = filter_item,
				Description = adict.get('Description', filter_item.upper())
			)
			vcf.add_filter_to_header(adict)

	contigs2drop = set()
	if pool['contig']:
		if path.isfile(reffai):
			refcontigs = getContigsFromFai(reffai)
		elif path.isfile(refdict):
			refcontigs = getContigsFromDict(refdict)
		else:
			refcontigs = {contig_item: 999999999 for contig_item in pool['contig']}

		for contig_item in pool['contig']:
			if contig_item not in vcf.seqnames:
				contig_len = refcontigs.get(contig_item, 999999999)
				vcf.add_to_header("##contig=<ID=%s,length=%s>" % (contig_item, contig_len))

	writer = Writer(outfile, vcf)
	#vcf.close()

	for variant in vcf:
		if variant.CHROM in contigs2drop:
			continue
		writer.write_record(variant)
	writer.close()

else:
	shell.mv(infile, outfile)
