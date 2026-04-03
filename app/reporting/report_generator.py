import json
from jinja2 import Template

def generate_json(diffs):
    return [
        {
            "type": d.element_type,
            "change": d.change_type,
            "base": d.base_value,
            "revised": d.revised_value,
            "bbox": d.bbox,
            "revised_bbox": getattr(d, "revised_bbox", None)
        }
        for d in diffs
    ]


def generate_html(diffs, output_path="output/report.html"):
    template = """
    <html>
    <body>
    <h2>Difference Report</h2>
    <table border="1">
    <tr><th>Type</th><th>Change</th><th>Base</th><th>Revised</th></tr>
    {% for d in diffs %}
    <tr>
        <td>{{d.element_type}}</td>
        <td>{{d.change_type}}</td>
        <td>{{d.base_value}}</td>
        <td>{{d.revised_value}}</td>
    </tr>
    {% endfor %}
    </table>
    </body>
    </html>
    """

    html = Template(template).render(diffs=diffs)

    with open(output_path, "w") as f:
        f.write(html)