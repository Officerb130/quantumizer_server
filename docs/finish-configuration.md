## Final configuration steps 

1. Update the [atlas configuration](../iress-atlas-software-isf-task-service.yaml) and set the following fields, once known. Note the majority of the fields have been defaulted these should be constantly reviewed as the service evolves.

    * hq-reference
    * sli-slo-sla
    * analysis-doc-link
    * dashboard-link

2. Update the [BuildKite pipeline.yml](../.buildkite/pipeline.yml) to ensure the correct target environments are being deployed to an uncomment the `make deployment__appear` step.

3. If no longer required delete the [finish-configuration.md](finish-configuration.md).

You can now start adding additional service level resources as required.