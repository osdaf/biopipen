import sys


{{ genenorm }}
{{ write.bedx.py }}

# get the genes
genes, _ = genenorm(
	{{in.infile | quote}}, 
	notfound = {{args.notfound | quote}},
	frm      = {{args.frm | quote}},
	to       = "genomic_pos_{{args.genome}},symbol",
	genome   = {{args.genome | quote}},
	tmpdir   = {{args.tmpdir | quote}},
	inopts   = {{args.inopts}},
	inmeta   = {{args.inmeta | lambda x: x if isinstance(x, list) or isinstance(x, dict) else '"' + x + '"'}}
)

writer = writeBedx({{out.outfile | quote}})
writer.meta.add(QUERY = 'The query gene name')
writer.writeHead()
for gene, hit in genes.items():
	pos      = hit['genomic_pos_{{args.genome}}']
	r        = readRecord()
	r.CHR    = 'chr' + str(pos['chr'])
	if pos['strand'] == 1:
		r.STRAND = '+'
		r.START  = pos['start'] - {{args.up}}
		r.END    = pos['start'] + {{args.down}}
		r.END    = {% if args.incbody %}max(r.END, pos['end']){% endif %}
	else:
		r.STRAND = '-'
		r.END    = pos['end'] + {{args.up}}
		r.START  = pos['end'] - {{args.down}}
		r.START  = {% if args.incbody %}min(r.START, pos['start']){% endif %}
	
	r.NAME   = hit['symbol']
	r.SCORE  = '0'
	r.QUERY  = gene
	writer.write(r)
