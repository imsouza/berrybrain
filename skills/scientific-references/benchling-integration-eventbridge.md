---
id: sciref-benchling-integration-eventbridge
name: "Scientific Ref: Benchling Events via AWS EventBridge"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (benchling-integration): Benchling Events via AWS EventBridge"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "benchling integration eventbridge"
  - "benchling events via aws eventbridge"
keywords:
  - "benchling"
  - "integration"
  - "eventbridge"
  - "specialized"
  - "scientific"
  - "reference"
---

# Benchling Events via AWS EventBridge

Integrations that react to supported Benchling changes, including entity registration and
workflow updates. Reviewed 2026-09-30. Payloads and AWS deployment snippets are illustrative;
no tenant subscription or deployment was tested. Event names below were checked against
the current EventBridge reference and SDK 1.25.0 event models.

**Official docs:**
- [Getting Started with Events](https://docs.benchling.com/docs/events-getting-started)
- [Events Reference (payloads and event types)](https://docs.benchling.com/docs/events-reference)
- [Events FAQs](https://docs.benchling.com/docs/events-faqs)
- [List Events API](https://benchling.com/api/reference#/Events/listEvents)

**Delivery methods:** Benchling supports **Webhooks** (recommended for new apps) and **AWS EventBridge** (customer-owned event bus). EventBridge payloads are **hydrated** (full v2 API objects in `detail`); webhooks use thinner payloads. See the getting-started guide for trade-offs.

---

## Setup checklist

1. **Tenant admin** enables Developer Platform access and opens [Event Subscriptions](https://your-tenant.benchling.com/event-subscriptions) (Feature settings → Developer Console → Events).
2. Create a subscription with:
   - AWS account ID and region
   - Event bus name (e.g. `benchling-integrations`)
   - Event types to receive (see [Events Reference](https://docs.benchling.com/docs/events-reference))
3. **Immediately** associate the partner event source with a new EventBridge bus in AWS (within ~12 days or the source expires).
4. Create EventBridge rules with `detail-type` / `detail` filters and targets (Lambda, SQS, SNS, CloudWatch Logs).
5. Grant invoke permissions (`AWS::Lambda::Permission`, queue policies, etc.).
6. Validate with a CloudWatch Logs rule on the bus `source`, then trigger a test action in Benchling.

Subscription statuses: `Pending` (needs bus association), `Active`, `Expired` (resubscribe in Benchling).

---

## EventBridge event envelope

All EventBridge deliveries share this top-level shape. The resource body lives under `detail` under a key that varies by event (for example `entry`, `assayRun`, `request`).

```json
{
  "version": "0",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "detail-type": "v2.request.created",
  "source": "aws.partner/benchling.com/your-tenant/your-subscription-name",
  "account": "123456789012",
  "time": "2026-09-29T14:30:00.000000+00:00",
  "region": "us-west-2",
  "resources": [],
  "detail": {
    "id": "evt_abc123",
    "eventType": "v2.request.created",
    "createdAt": "2026-09-29T14:30:00.000000+00:00",
    "deprecated": false,
    "excludedProperties": [],
    "schema": {
      "id": "ts_abc123",
      "name": "Validated Request"
    },
    "request": {
      "id": "req_example",
      "name": "Sequencing request",
      "apiURL": "https://your-tenant.benchling.com/api/v2/requests/req_example"
    }
  }
}
```

**Naming:** `detail-type` and `detail.eventType` follow `<version>.<resource>.<action>` (for example `v2.request.created`, `v2.workflowTask.updated.status`).

**Do not treat payloads as authoritative.** Events may arrive late or out of order. Re-fetch objects with the SDK/API when you need current state.

**Truncated events:** Benchling documents a 256 KB EventBridge payload threshold.
Inspect `detail.excludedProperties`. Re-fetch by ID through the configured tenant SDK;
do not send credentials to an arbitrary `apiURL` from an event.

---

## Minimal EventBridge rule (CloudFormation)

Route `v2.request.created` events for a specific request schema to a Lambda:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Benchling request.created → Lambda

Parameters:
  BenchlingEventBusName:
    Type: String
    Description: Partner event bus name from Benchling subscription

Resources:
  RequestCreatedRule:
    Type: AWS::Events::Rule
    Properties:
      Name: benchling-request-created
      EventBusName: !Ref BenchlingEventBusName
      State: ENABLED
      EventPattern:
        detail-type:
          - v2.request.created
        detail:
          schema:
            name:
              - Validated Request
      Targets:
        - Id: HandleRequestCreated
          Arn: !GetAtt HandleEventLambda.Arn

  HandleEventLambda:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      Runtime: python3.12
      CodeUri: src/
      Timeout: 30

  AllowEventBridgeInvoke:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref HandleEventLambda
      Principal: events.amazonaws.com
      SourceArn: !GetAtt RequestCreatedRule.Arn
```

**Other filter examples** (from Benchling docs):

```json
{
  "detail-type": ["v2.assayRun.updated.fields"],
  "detail": {
    "updates": ["fields.my_field"]
  }
}
```

```json
{
  "detail-type": ["v2.entity.registered"],
  "detail": {
    "entity": {
      "schema": {
        "id": ["ts_MySchemaId"]
      }
    }
  }
}
```

---

## Lambda handler skeleton (Python)

```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Optional: re-fetch via SDK when payload may be stale or truncated
# import os
# from benchling_sdk.benchling import Benchling
# from benchling_sdk.auth.api_key_auth import ApiKeyAuth
#
# benchling = Benchling(
#     url=os.environ["BENCHLING_TENANT_URL"],
#     auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"]),
# )


def handler(event, context):
    """Process a single Benchling EventBridge delivery."""
    detail_type = event.get("detail-type")
    detail = event.get("detail") or {}

    logger.info(
        "benchling_event",
        extra={
            "detail_type": detail_type,
            "event_id": detail.get("id"),
            "benchling_event_type": detail.get("eventType"),
        },
    )

    if detail.get("deprecated"):
        logger.warning("deprecated_event_type: %s", detail_type)

    if detail.get("excludedProperties"):
        logger.warning(
            "truncated_payload excluded=%s", detail.get("excludedProperties")
        )

    if detail_type == "v2.request.created":
        request = detail.get("request") or {}
        request_id = request.get("id")
        if not request_id:
            raise ValueError("missing request.id in event detail")
        # Prefer API lookup for authoritative data:
        # current = benchling.requests.get_by_id(request_id)
        return {"status": "obs

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

