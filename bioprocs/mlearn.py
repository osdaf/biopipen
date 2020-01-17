"""Machine learning processes"""
from diot import Diot
from . import params, proc_factory

# pylint: disable=invalid-name

pRegressTrain = proc_factory(
    desc='Train a regression model',
    config=Diot(annotate="""
    @name:
        pRegressTrain
    @description:
        Train a regression model
    @input:
        `infile:file`: The input file (regression done on columns)
        `fmfile:file`: The file defining the regression formula.
            ```
            Case1   lm   Y ~ X1 + X2
            Case2   glm  Y ~ X1 + X2 + X1:X2
            ```
            - `Case` column can be omitted, if so, `Case1`, `Case2` will be added automatically.
            - No head.
        `casefile:file`: Defining cases:
            ```
            R1   Case1
            R2   Case1
            ... ...
            Rm   Case1
            Rm   Case2
            Rm+1 Case2
            ... ...
            Rn   Case2
            ```
            - One row can bed used for multiple cases
            - No head.
    @output:
        `outfile:file`: The output file with the summary of the models
        `outdir:dir`  : The output directory containing the summaries, models and plots
    @args:
        `plot`   : Plot the model? Default: `False`
        `inopts` : Input options for input file. Default: `Diot(cnames = True, rnames = True)`
        `devpars`: The device parameters for the plot. Default: `Diot(res = 300, height = 4000, width = 4000)`
    """),
    input='infile:file, fmfile:file, casefile:file',
    output=[
        'outfile:file:{{i.infile | fn2}}.regress/'
        '{{i.infile | fn2}}.regress.txt',
        'outdir:dir:{{i.infile | fn2}}.regress'
    ],
    lang=params.Rscript.value,
    args=Diot(
        plot=False,
        cov='',
        yval='numeric',
        save=True,
        glmfam='binomial',
        inopts=Diot(rnames=True, cnames=True),
        devpars=Diot(res=300, height=4000, width=4000),
    ),
)

pRegressPred = proc_factory(
    desc='Use a trained linear regression model to predict',
    config=Diot(annotate="""
    @name:
        pRegressPred
    @description:
        Use a trained linear regression model to predict
    @input:
        `infile:file`: The input file
        `model:file` : The trained model by `pRegressTrain`.
            - It can also be a directory containing models generated by `pRegressTrain`.
            - We will scan the model with file name: `*.<model>.rds`
            - Models have to be on the same column.
    @output:
        `outfile:file`: The output file, a copy of infile with Case, predicted value and items in `args.out` added.
        `outdir:dir`  : The output directory
    @args:
        `inopts` : The input options.
        `out`    : What to include in the output file
            - `prob`: Output the probabilities. Default: `True`
            - `auc` : Output AUCs. Default: `True` (only when Y column exists in infile)
            - If `auc` is True, then ROC is anyway plotted.
        `plot`   : Parameters to plot the ROC. Use `False` to disable. Default: `False`
            - Enabled only when Y column exists in infile
            - Could be a dict (Diot) with keys:
            - `labels`:  show labels or not
            - `showAUC`: show AUC or not
            - `combine`: combine all roc in one figure?
        `ggs`    : The ggs items to be added for the plot. Default:
            ```Diot({
                'style_roc': {},
                # show legend at bottom right corner
                'theme#auc': {'legend.position': [1, 0], 'legend.justification': [1, 0]}
            })```
        `devpars`: The device parameters for the plot. Default: `Diot(res = 300, height = 2000, width = 2000)`
        `inopts` : Options for reading the input file. Default: `Diot(cnames = True, rnames = True, delimit = "\t")`
    """),
    input='infile:file, model:file',
    output=[
        'outfile:file:{{i.infile | fn2}}.pred/{{i.infile | fn2}}.pred.txt',
        'outdir:dir:{{i.infile | fn2}}.pred'
    ],
    lang=params.Rscript.value,
    args=Diot(
        out=Diot(prob=True, auc=True),
        plot=Diot(labels=False, showAUC=True, combine=True),
        ggs=Diot({
            'style_roc': {},
            # show legend at bottom right corner
            'theme#auc': {
                'legend.position': [1, 0],
                'legend.justification': [1, 0]
            }
        }),
        devpars=Diot(res=300, height=2000, width=2000),
        inopts=Diot(cnames=True, rnames=True, delimit="\t")
    ),
)

pGlmTrain = proc_factory(
    desc='Train a logistic regression model',
    config=Diot(annotate="""
    @input:
        infile: The input file (Last column as Y)
    @output:
        outmodel: The output model (RData file)
        outdir  : The output directory containing model, plots and other files
    @args:
        plot   : Whether plot the glm probability. Default: `True`
        formula: The formula to perform the regression. Default: `None`.
            - If `None`, will use all first N-1 columns as features.
        inopts : The input options.
        yval   : The type of y values. Default: `categ`
            - `categ`  : categorical values
            - `prob`   : probabilities
            - `numeric`: numeric values
        devpars: The device parameters for the plot.
    """),
    lang=params.Rscript.value,
    input='infile:file',
    output=[
        'outmodel:file:{{i.infile | stem}}.glm/{{i.infile | stem}}.glm.RDS',
        'outdir:dir:{{i.infile | stem}}.glm'
    ],
    args=Diot(plot=True,
              formula=None,
              devpars=Diot(res=300, height=2000, width=2000),
              params=Diot(family='binomial'),
              ggs=Diot(geom_smooth=Diot({
                  "method": "glm",
                  "method.args": Diot(family="binomial"),
                  "se": True
              })),
              inopts=Diot(cnames=True, rnames=True, delimit="\t"),
              yval='categ')
)

pGlmTest = proc_factory(
    desc='Test trained logistic regression model',
    config=Diot(annotate="""
    @input:
        `infile:file`: The input file
        `model:file` : The trained model by `pLogitRegTrain`
    @output:
        `outdir:dir`: The output directory
    @args:
        `inopts` : The input options.
        `outprob`: Also output probabilities? Default: True
    """),
    lang=params.Rscript.value,
    input='infile:file, model:file',
    output='outdir:dir:{{i.infile | stem}}.glm.test',
    args=Diot(outprob=True,
              outauc=True,
              params=Diot(),
              ggs=Diot(),
              devpars=Diot(res=300,
                           height=2000,
                           width=2000),
              inopts=Diot(cnames=True,
                          rnames=True,
                          delimit="\t"))
)

pRandomForestTrain = proc_factory(
    desc="Train a random forest model.",
    config=Diot(annotate="""
    @input:
        `infile:file`: The input file (Last column as Y)
    @output:
        `outmodel:file`: The output model (RData file)
        `outdir:dir`   : The output directory containing model, plots and other files
    @args:
        `plot`   : Whether plot the feature importance. Default: `True`
        `formula`: The formula to perform the regression. Default: `None`.
            - If `None`, will use all first N-1 columns as features.
        `inopts` : The input options.
        `na`     : Replace NAs with? Default: `0`
        `devpars`: The device parameters for the plot.
    @requires:
        `r-randomForst`
    """),
    input='infile:file',
    output=[
        'outmodel:file:{{i.infile | stem}}.rforest/'
        '{{i.infile | stem}}.rforest.rds',
        'outdir:dir:{{i.infile | stem}}.rforest'
    ],
    lang=params.Rscript.value,
    args=Diot(plot=True,
              formula=None,
              params=Diot(importance=True),
              na=0,
              devpars=Diot(res=300, height=2000, width=2000),
              inopts=Diot(cnames=True, rnames=True, delimit="\t")),
)

pRandomForestTest = proc_factory(
    desc='Test trained random forest model',
    config=Diot(annotate="""
    @input:
        `infile:file`: The input file
        `model:file` : The trained model by `pLogitRegTrain`
    @output:
        `outdir:dir`: The output directory
    @args:
        `inopts` : The input options.
        `outprob`: Also output probabilities? Default: True
    """),
    lang=params.Rscript.value,
    input='infile:file, model:file',
    output='outdir:dir:{{i.infile | stem}}.rf.test',
    args=Diot(outprob=True,
              outauc=True,
              params=Diot(),
              ggs=Diot(),
              devpars=Diot(res=300, height=2000, width=2000),
              inopts=Diot(cnames=True, rnames=True, delimit="\t"))
)

pDecisionTreeTrain = proc_factory(
    desc="Train a decision tree model",
    config=Diot(annotate="""
    @name:
        pDecisionTreeTrain
    @description:
        Train a decision tree model
    @input:
        `infile:file`: The input file (Last column as Y)
    @output:
        `outmodel:file`: The output model (RData file)
        `outdir:dir`   : The output directory containing model, plots and other files
    @args:
        `plot`   : Whether plot the feature importance. Default: `True`
        `formula`: The formula to perform the regression. Default: `None`.
            - If `None`, will use all first N-1 columns as features.
        `inopts` : The input options.
        `na`     : Replace NAs with? Default: `0`
        `devpars`: The device parameters for the plot. Default: `Diot(res = 300, height = 2000, width = 2000)`
    @requires:
        `r-rpart`
    """),
    input='infile:file',
    output=[
        'outmodel:file:{{i.infile | stem}}.dtree/{{i.infile | stem}}.dtree.rds',
        'outdir:dir:{{i.infile | stem}}.dtree'
    ],
    lang=params.Rscript.value,
    args=Diot(plot=True,
              formula=None,
              na=0,
              devpars=Diot(res=300, height=2000, width=2000),
              inopts=Diot(cnames=True, rnames=True, delimit="\t")),
)

pCrossValid = proc_factory(
    desc='Cross validation on the model',
    config=Diot(annotate="""
    @input:
        `infile:file`: The input data file.
    @output:
        `outmodel:file`: The trained model in RDS format
        `outdir:dir`   : The output directory containing output model and plots.
    @args:
        `inopts` : The options to read the input file.
        `ctrl`   : Arguments for `trainControl`.
            - See https://topepo.github.io/caret/model-training-and-tuning.html#the-traincontrol-function
            - Available methods: "boot", "cv", "LOOCV", "LGOCV", "repeatedcv", "timeslice", "none" and "oob"
        `train`  : Arguments for `train` other than `data` and `trControl`.
            - See https://topepo.github.io/caret/model-training-and-tuning.html#basic-parameter-tuning
            - form: formula of the model,
            - method: rf, glm, etc
        `seed`   : The seed.
        `nthread`: # threads to use.
        `plots`  : Do types of plots.
            - `varimp` also available
            - You can also concatenate them using comma (`,`)
    @requires:
        `r-caret`
    """),
    lang=params.Rscript.value,
    input='infile:file',
    output=[
        'outmodel:file:{{i.infile | fn2}}.{{args.train.method}}/'
        '{{i.infile | fn2}}.{{args.train.method}}.RDS',
        'outdir:dir:{{i.infile | fn2}}.{{args.train.method}}'
    ],
    args=Diot(
        inopts=Diot(cnames=True, rnames=True),
        ctrl=Diot(method='',
                  savePredictions=True,
                  classProbs=True,
                  verboseIter=True),
        train=Diot(form=None, method='', metric='ROC'),
        seed=None,
        nthread=1,
        plots=['model', 'roc'],  # varimp
        devpars=Diot(res=300, height=2000, width=2000)
    )
)

pSplitSamples = proc_factory(
    desc='Split samples for testing and training',
    lang=params.python.value,
    input='infile:file',
    output=[
        'trainfile:file:{{i.infile | stem}}.training{{i.infile | ext}}',
        'testfile:file:{{i.infile | stem}}.testing{{i.infile | ext}}'
    ],
    args=Diot(
        seed=0,
        inopts=Diot(cnames=True),
        method=
        '10-fold'  # leave-one, or a ratio for training and testing (i.e: 9:1)
    )
)
