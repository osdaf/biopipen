library(methods)
{{rimport}}('__init__.r')
options(stringsAsFactors = F)

infile   = {{i.infile | R}}
gfile    = {{i.groupfile | R}}
cfile    = {{i.casefile | R}}
outfile  = {{o.outfile | R}}
outdir   = {{o.outdir | R}}
pcut     = {{args.pval | R}}
dofdr    = {{args.fdr | R}}
plotchow = {{args.plot | R}}
devpars  = {{args.devpars | R}}
ggs      = {{args.ggs | R}}
inopts   = {{args.inopts | R}}
covfile  = {{args.cov | R}}

if (plotchow) {
	{{rimport}}('plot.r')
}

if (dofdr == T) dofdr = 'BH'

regress = function(regdata, name, fmula) {
	m = lm(as.formula(fmula), data = regdata)
	list(model = m, ssr = sum(m$residuals ^ 2), n = nrow(regdata), name = name)
}

formlm = function(model, k, withname = T) {
	lencoef = length(model$model$coefficients)
	coefns  = c(names(model$model$coefficients)[(lencoef-k+2):lencoef], '_')
	coeffs  = as.numeric(c(model$model$coefficients[(lencoef-k+2):lencoef], model$model$coefficients[1]))
	coefns  = c(coefns, "N")
	coeffs  = c(coeffs, model$n)
	if (withname) {
		paste0(model$name, ':', paste(coefns, round(coeffs, 3), sep = '=', collapse = ','))
	} else {
		paste(coefns, round(coeffs, 3), sep = '=', collapse = ',')
	}
}

chow = function(pooled, subregs, k, case) {
	subssr  = sum(sapply(subregs, function(x) x$ssr))
	ngroups = length(subregs)
	J  = (ngroups - 1) * k
	DF = pooled$n - ngroups * k
	FS = (pooled$ssr - subssr) * DF / subssr / J
	groups = lapply(subregs, function(m) formlm(m, k))
	pooledm = formlm(pooled, k, FALSE)
	list(Case = case, Pooled = pooledm, Groups = paste(groups, collapse = '; '), Fstat = FS, Pval = pf(FS, J, DF, lower.tail = FALSE))
}

model2eq = function(model) {
	vars = colnames(model$model)
	cf   = sapply(model$coefficients, function(f) {
		if (is.na(f)) return("NA")
		f = round(f, 2)
		if (f >= 0) return(paste0("+", f))
		return(paste0("-", -f))
	})
	paste0(vars[1], ' = ', cf[1], paste(
		sapply(
			2:length(cf),
			function(x) paste0(cf[x], '*', vars[x])
		), collapse = ''
	))
}
results = data.frame(
	Case   = character(),
	Pooled = character(),
	Groups = character(),
	Fstat  = double(),
	Pval   = double()
)

indata = read.table.inopts(infile, inopts, try = TRUE)
if (is.null(indata)) {
	write.table(results, outfile, col.names = T, row.names = F, sep = "\t", quote = F)
	quit(save = "no")
}

#     X1  X2  X3  X4 ... Y
# G1  1   2   1   4  ... 9
# G2  2   3   1   1  ... 3
# ... ...
# Gm  3   9   1   7  ... 8
#K = ncol(indata)
if (covfile != "") {
	covdata = read.table(covfile, header = T, row.names = 1, check.names = F)
	indata  = cbind(covdata[rownames(indata),,drop = F], indata)
}
gdata  = read.table.inopts(gfile, list(cnames = TRUE, rnames = TRUE))
# 	Case1	Case2
# G1	Group1	Group1
# G2	Group1	NA
# G3	Group2	Group1
# ... ...
# Gm	Group2	Group2
cases  = colnames(gdata)
fmulas = data.frame(x = rep(paste(bQuote(colnames(indata)[ncol(indata)]), '~ .'), length(cases)))
rownames(fmulas) = cases
if (!is.null(cfile) && cfile != "") {
	fmulas = read.table.inopts(cfile, list(cnames = FALSE, rnames = TRUE))
	cases  = rownames(fmulas)
}

for (case in cases) {
	fmula     = fmulas[case,,drop = TRUE]
	allvars   = all.vars(as.formula(fmula))
	if (allvars[2] == '.') {
		K = ncol(indata)
	} else {
		K = length(allvars)
	}
	subgroups = levels(as.factor(gdata[, case]))
	pooled_lm = regress(
		indata[rownames(gdata[which(gdata[,case] %in% subgroups), case, drop = F]),,drop = F], 
		name = 'Pooled', fmula = fmula)
	subgrp_lm = lapply(subgroups, function(sgroup) {
		sdata = indata[rownames(gdata[which(gdata[,case] == sgroup), case, drop = F]),,drop = F]
		if (nrow(sdata) < 3) NULL
		else regress(sdata, name = sgroup, fmula = fmula)
	})
	subgrp_lm[sapply(subgrp_lm, is.null)] <- NULL
	# no subgroups
	if (length(subgrp_lm) < 2) next
	ret = chow(pooled_lm, subgrp_lm, k = K, case = case)
	if (is.na(ret$Pval) || ret$Pval >= pcut) next
	results = rbind(results, ret)

	# doplot
	if (plotchow) {
		incol = ncol(indata)
		plotdata = cbind(
			indata[rownames(gdata[which(gdata[,case] %in% subgroups), case,drop = F]),,drop = F], 
			Group = na.omit(gdata[,case]))
		rcase = make.names(case)
		colnames(plotdata)[incol + 1] = rcase

		labels = sapply(c(subgrp_lm, list(pooled_lm)), function(m) paste0(m$name, ': ', model2eq(m$model), ' (N=', m$n, ')'))
		if (!is.null(ggs$scale_color_manual) && !is.null(ggs$scale_color_manual$labels)) {
			if (is.function(ggs$scale_color_manual$labels)) {
				labels = ggs$scale_color_manual$labels(labels)
			} else {
				labels = ggs$scale_color_manual$labels
			}
		}
		ggs1 = c(ggs, list(
			geom_smooth = list(
				aes(color = 'Pooled'),
				method   = 'lm',
				se       = F,
				linetype = "twodash"
			),
			geom_smooth = list(
				aes_string(color = rcase),
				method  = 'lm',
				se      = F
			),
			theme = list(
				legend.position = "bottom"
			),
			guides = list(
				color=guide_legend(ncol=1),
				shape=F
			),
			scale_color_manual = list(
				values = c(scales::hue_pal()(length(subgroups)), '#555555'), 
				name   = "",
				limit  = c(subgroups, 'Pooled'),
				labels = labels
			)
		))
		pcnames = colnames(plotdata)
		plot.scatter(
			plotdata, 
			file.path(outdir, paste0(case, '.png')), 
			x      = ifelse(allvars[2] == '.', pcnames[1], which(allvars[2] == pcnames)),
			y      = which(allvars[1] == pcnames),
			ggs    = ggs1,
			params = list(aes_string(shape = rcase, color = rcase))
		)
	}
}

if (dofdr != F) {
	results = cbind(results, Qval = p.adjust(results$Pval, method = dofdr))
} 
write.table(pretty.numbers(results, list(
	Fstat      = '%.3f',
	Pval..Qval = '%.3E'
)), outfile, col.names = T, row.names = F, sep = "\t", quote = F)

