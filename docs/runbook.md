More can be read about Runbooks [here](https://wa.aws.amazon.com/wat.concept.runbook.en.html)

# Required Access

Access to the following systems are required:

* Buildkite and the [build pipeline](https://buildkite.com/https://buildkite.com/oneiress/isf-task-service)
* Datadog (Staging, UAT and Production)
* Github [repo](https://github.com/oneiress/isf-task-service)
* Kialli dashboard for the relevant environment/account
* kubernetes dashboard for the relevant environment/account

# Deployment

The deployment and infrastructure is defined in the Github [repo](https://github.com/oneiress/isf-task-service), and deployment is done via the Buildkite [build pipeline](https://buildkite.com/https://buildkite.com/oneiress/isf-task-service).

The pipeline currently builds, tests and deploys the service to _Staging_ after which promoting to _UAT_ and _Production_ requires manual intervention/approval. 

# API health

Datadog monitors are created by the code as part of the deployment. The monitors will send a slack message to the `#slack_channel_name_here` channel and monitor the following:

* TBD
* TBD
* ...



