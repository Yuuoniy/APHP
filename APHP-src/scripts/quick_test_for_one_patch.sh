#!/bin/bash
cd /root/APHP/APHP-src/SpecificationExtraction/
python runner_for_specs_extract.py one kernel e5548b05631e
cd /root/APHP/APHP-src/BugDetection/
python /root/APHP/APHP-src/BugDetection/bug_detect.py test_spec_for_one_func usb_create_hcd dwc2_hcd_init