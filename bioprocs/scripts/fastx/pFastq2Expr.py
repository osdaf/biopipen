from pyppl import Box
from bioprocs.utils import cmdargs, runcmd
from bioprocs.utils.tsvio import TsvReader, TsvWriter

params = {{args.params}}
params['i'] = {{args.idxfile | quote}}
params['o'] = {{out.outdir | quote}}
params['t'] = {{args.nthread}}

cmd = '{{args.kallisto}} quant %s "{{in.fqfile1}}" "{{in.fqfile2}}"' % (cmdargs(params))
runcmd (cmd)

imfile  = "{{out.outdir}}/abundance.tsv"
outfile = {{out.outfile | quote}}
reader  = TsvReader(imfile, ftype = 'head')
writer  = TsvWriter(outfile)
writer.meta.add('target_id', 'est_counts')
writer.writeHead()
for r in reader:
    r.target_id  = r.target_id.split('::')[0]
    try:
        r.est_counts = int(round(float(r.est_counts)))
    except TypeError:
        r.est_counts = 0
    writer.write(r)
