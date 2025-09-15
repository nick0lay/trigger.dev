We can get logs only from deployment logs, like this:
```
query GetDeploymentLogs {
  deploymentLogs(
    deploymentId: "895235d1-84ed-41cd-9871-e17a3be8bf12"
    filter: "allChildQueuesByScore"
    limit: 2
  ) {
    message
    timestamp
    severity
  }
}
```
Response:
```
{
  "data": {
    "deploymentLogs": [
      {
        "message": "allChildQueuesByScore",
        "timestamp": "2025-09-14T20:36:34.162869912Z",
        "severity": "info"
      },
      {
        "message": "allChildQueuesByScore",
        "timestamp": "2025-09-14T20:36:35.679486438Z",
        "severity": "info"
      },
      {
        "message": "allChildQueuesByScore",
        "timestamp": "2025-09-14T20:36:38.176964299Z",
        "severity": "info"
      }
    ]
  }
}
```

Find last sucessful deployment id:
```
query GetDeployment {
  deployments(
    input: {environmentId: "c7a252c8-9a7d-468b-b429-e567bc328424", projectId: "5172cd2b-e599-49ff-9bf2-42ec175e61f5", serviceId: "ad419629-804e-46da-ab80-61d3b5c09f80", status: {in: SUCCESS}}
    last: 1
  ) {
    edges {
      node {
        id
      }
    }
  }
}
```
Response:
```
{
  "data": {
    "deployments": {
      "edges": [
        {
          "node": {
            "id": "895235d1-84ed-41cd-9871-e17a3be8bf12"
          }
        }
      ]
    }
  }
}
```

Since we need to get service id somehow, which we know only after deployment, we had to lookup service id by name. This query will return all project services.
```
query GetProjectServices {
  project(id: "5172cd2b-e599-49ff-9bf2-42ec175e61f5") {
    services {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
```
Response:
```
{
  "data": {
    "project": {
      "services": {
        "edges": [
          {
            "node": {
              "id": "63a9ee3f-2c67-4eb7-9b08-9baac2bc37af",
              "name": "registry"
            }
          },
          {
            "node": {
              "id": "94d5daa2-9ec3-4572-bf0d-5f9a98e2f334",
              "name": "Redis"
            }
          },
          {
            "node": {
              "id": "ad419629-804e-46da-ab80-61d3b5c09f80",
              "name": "webapp"
            }
          },
          {
            "node": {
              "id": "cdd033c6-680f-4943-93f6-ba75d9c87c07",
              "name": "minio"
            }
          },
          {
            "node": {
              "id": "d8a60e32-7f49-4ae0-b93b-2ea4e489eb17",
              "name": "ClickHouse"
            }
          },
          {
            "node": {
              "id": "de998cea-a2ef-464c-b18d-253a39d3ef8a",
              "name": "Postgres"
            }
          },
          {
            "node": {
              "id": "e77e8d53-8228-42d8-99b8-bb1e97dab80d",
              "name": "docker-socket-proxy"
            }
          },
          {
            "node": {
              "id": "f85b676d-299c-427f-b1ff-45e6bbdcbc5f",
              "name": "supervisor"
            }
          }
        ]
      }
    }
  }
}
```