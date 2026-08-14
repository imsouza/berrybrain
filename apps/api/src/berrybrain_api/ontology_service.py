from __future__ import annotations

from importlib.resources import files
from typing import Any

from pyshacl import validate
from rdflib import DCTERMS, RDF, RDFS, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, PROV, SH, SKOS, XSD
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.artifact_state import accepted_edge_clause, accepted_node_clause
from berrybrain_api.graph_ontology import ontology_class, ontology_property
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord

BB = Namespace("https://berrybrain.app/ns#")
SCHEMA = Namespace("https://schema.org/")
ONTOLOGY_IRI = URIRef("https://berrybrain.app/ontology/1.4.8")
ONTOLOGY_VERSION = "1.4.8"

PREFIXES: dict[str, Namespace] = {
    "bb": BB,
    "dcterms": DCTERMS,
    "owl": OWL,
    "prov": PROV,
    "rdf": RDF,
    "rdfs": RDFS,
    "schema": SCHEMA,
    "skos": SKOS,
    "xsd": XSD,
}

JSON_LD_CONTEXT = {
    "@version": 1.1,
    "bb": str(BB),
    "dcterms": str(DCTERMS),
    "owl": str(OWL),
    "prov": str(PROV),
    "rdf": str(RDF),
    "rdfs": str(RDFS),
    "schema": str(SCHEMA),
    "skos": str(SKOS),
    "xsd": str(XSD),
    "label": "rdfs:label",
    "nodeType": "bb:nodeType",
    "edgeType": "bb:edgeType",
    "stableId": "bb:stableId",
    "qualityStatus": "bb:qualityStatus",
    "subject": {"@id": "bb:subject", "@type": "@id"},
    "predicate": {"@id": "bb:predicate", "@type": "@id"},
    "object": {"@id": "bb:object", "@type": "@id"},
}


def expand_curie(value: str) -> URIRef:
    prefix, separator, local_name = str(value or "").partition(":")
    if not separator or not local_name or prefix not in PREFIXES:
        raise ValueError(f"Unsupported ontology identifier: {value}")
    return URIRef(PREFIXES[prefix][local_name])


def build_knowledge_graph(
    session: Session, *, include_provisional: bool = False
) -> Graph:
    graph = Graph(identifier=ONTOLOGY_IRI)
    for prefix, namespace in PREFIXES.items():
        graph.bind(prefix, namespace)

    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(
                accepted_node_clause(include_provisional=include_provisional)
            )
        ).scalars()
    )
    node_by_id = {node.id: node for node in nodes}
    for node in nodes:
        subject = URIRef(node.iri)
        graph.add(
            (
                subject,
                RDF.type,
                expand_curie(node.ontology_class or ontology_class(node.type)),
            )
        )
        graph.add((subject, RDFS.label, Literal(node.label)))
        graph.add((subject, BB.stableId, Literal(node.stable_id)))
        graph.add((subject, BB.nodeType, Literal(node.type)))
        graph.add((subject, BB.qualityStatus, Literal(node.quality_gate_status)))
        if node.summary:
            graph.add((subject, DCTERMS.description, Literal(node.summary)))
        if node.confidence_sample_size:
            graph.add(
                (subject, BB.confidence, Literal(node.confidence, datatype=XSD.decimal))
            )

    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                accepted_edge_clause(include_provisional=include_provisional)
            )
        ).scalars()
    )
    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        if source is None or target is None:
            continue
        source_iri = URIRef(source.iri)
        target_iri = URIRef(target.iri)
        predicate = expand_curie(edge.ontology_property or ontology_property(edge.type))
        assertion = URIRef(edge.iri)
        graph.add((source_iri, predicate, target_iri))
        graph.add((assertion, RDF.type, BB.Assertion))
        graph.add((assertion, BB.stableId, Literal(edge.stable_id)))
        graph.add((assertion, BB.subject, source_iri))
        graph.add((assertion, BB.predicate, predicate))
        graph.add((assertion, BB.object, target_iri))
        graph.add((assertion, BB.edgeType, Literal(edge.type)))
        graph.add((assertion, BB.qualityStatus, Literal(edge.quality_gate_status)))
        if edge.reason:
            graph.add((assertion, DCTERMS.description, Literal(edge.reason)))
        if edge.confidence_sample_size:
            graph.add(
                (
                    assertion,
                    BB.confidence,
                    Literal(edge.confidence, datatype=XSD.decimal),
                )
            )
    return graph


def serialize_knowledge_graph(
    session: Session,
    *,
    output_format: str = "json-ld",
    include_provisional: bool = False,
) -> str:
    graph = build_knowledge_graph(session, include_provisional=include_provisional)
    if output_format == "json-ld":
        return str(
            graph.serialize(
                format="json-ld",
                context=JSON_LD_CONTEXT,
                auto_compact=True,
                indent=2,
            )
        )
    if output_format == "turtle":
        return str(graph.serialize(format="turtle"))
    raise ValueError(f"Unsupported ontology export format: {output_format}")


def validate_knowledge_graph(
    session: Session, *, include_provisional: bool = False
) -> dict[str, Any]:
    data_graph = build_knowledge_graph(session, include_provisional=include_provisional)
    ontology_graph = Graph().parse(_ontology_path(), format="turtle")
    shapes_graph = Graph().parse(_shapes_path(), format="turtle")
    conforms, results_graph, _results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ontology_graph,
        inference="rdfs",
        advanced=True,
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )
    violations: list[dict[str, str]] = []
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        focus_node = results_graph.value(result, SH.focusNode)
        path = results_graph.value(result, SH.resultPath)
        message = results_graph.value(result, SH.resultMessage)
        severity = results_graph.value(result, SH.resultSeverity)
        violations.append(
            {
                "focusNode": str(focus_node or ""),
                "path": str(path or ""),
                "message": str(message or "Ontology validation failed."),
                "severity": _compact_identifier(str(severity or "")),
            }
        )
    return {
        "conforms": bool(conforms),
        "ontologyVersion": ONTOLOGY_VERSION,
        "tripleCount": len(data_graph),
        "violationCount": len(violations),
        "violations": violations,
    }


def ontology_metadata() -> dict[str, Any]:
    return {
        "iri": str(ONTOLOGY_IRI),
        "version": ONTOLOGY_VERSION,
        "namespace": str(BB),
        "formats": ["json-ld", "turtle"],
        "validation": "SHACL Core and SHACL-SPARQL with RDFS inference",
    }


def _ontology_path() -> str:
    return str(files("berrybrain_api").joinpath("ontology/berrybrain.ttl"))


def _shapes_path() -> str:
    return str(files("berrybrain_api").joinpath("ontology/berrybrain-shapes.ttl"))


def _compact_identifier(value: str) -> str:
    for prefix, namespace in PREFIXES.items():
        namespace_value = str(namespace)
        if value.startswith(namespace_value):
            return f"{prefix}:{value.removeprefix(namespace_value)}"
    return value
