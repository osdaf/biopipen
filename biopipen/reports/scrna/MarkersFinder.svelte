{% from "utils/misc.liq" import report_jobs -%}
<script>
    import { Image, DataTable } from "@@";
    import { Tabs, Tab, TabContent } from "carbon-components-svelte";
</script>


{%- macro report_job(job, h=1) -%}
{% for casedir in job.out.outdir | joinpaths: "*" | glob %}
{%  set case = casedir | basename %}
<h{{h}}>{{case}}</h{{h}}>

<h{{h+1}}>Markers</h{{h+1}}>
<DataTable
    src={{ casedir | joinpaths: "markers.txt" | quote }}
    data={ {{ casedir | joinpaths: "markers.txt" | datatable: sep="\t", nrows=100 }} }
    />

<h{{h+1}}>Enrichment analysis</h{{h+1}}>
<Tabs>
    {% for enrtxt in casedir | joinpaths: "Enrichr-*.txt" | glob %}
    {%  set db = enrtxt | stem | replace: "Enrichr-", "" %}
    <Tab label="{{db}}" title="{{db}}" />
    {% endfor %}
    <div slot="content">
        {% for enrtxt in casedir | joinpaths: "Enrichr-*.txt" | glob %}
        {%  set db = enrtxt | stem | replace: "Enrichr-", "" %}
        <TabContent>
            <Image src={{casedir | joinpaths: "Enrichr-" + db + ".png" | quote}} />
            <DataTable
                src={{ enrtxt | quote }}
                data={ {{ enrtxt | datatable: sep="\t", nrows=100 }} }
                />
        </TabContent>
        {% endfor %}
    </div>
</Tabs>

{% endfor %}
{%- endmacro -%}


{%- macro head_job(job) -%}
{% if job.in.name %}
<h1>{{job.in.name | escape}}</h1>
{% else %}
<h1>Case {{job.index | plus: 1 | str}}</h1>
{% endif %}
{%- endmacro -%}

{{ report_jobs(jobs, head_job, report_job) }}