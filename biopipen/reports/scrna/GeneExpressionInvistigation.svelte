{% from_ os import path %}
{% from "utils/misc.liq" import report_jobs, table_of_images -%}

<script>
    import { Image } from "@@";
</script>

{%- macro report_job(job, h=1) -%}

{% assign boxplotpng = job.out.outdir | joinpaths: "boxplot.png" %}
{% assign heatmappng = job.out.outdir | joinpaths: "heatmap.png" %}

{% if path.exists(boxplotpng) %}
<Image src={{boxplotpng | quote}} />
{% endif %}

{% if path.exists(heatmappng) %}
<Image src={{heatmappng | quote}} />
{% endif %}

{%- endmacro -%}

{%- macro head_job(job) -%}
{% assign config = job.in.configfile | read | toml_loads %}
{% assign name = config.name or stem(job.out.outdir) %}
<h1>{{name | escape}}</h1>
{%- endmacro -%}

{{ report_jobs(jobs, head_job, report_job) }}
