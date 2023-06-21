# APHP: API Post-Handling bugs detector


- [APHP: API Post-Handling bugs detector](#aphp-api-post-handling-bugs-detector)
  - [Description](#description)
  - [Structure](#structure)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Minimal running example](#minimal-running-example)
    - [Batch Testing](#batch-testing)
      - [A. Specifications Extraction Testing](#a-specifications-extraction-testing)
      - [B. Bug Detection Testing](#b-bug-detection-testing)
  - [Data for reference](#data-for-reference)
  - [Additional Notes](#additional-notes)
  - [About](#about)

## Description
This artifact houses the APHP tool, an API Post-Handling bugs detector designed for the paper titled "Detecting API Post-Handling Bugs Using Code and Description in Patches" (Usenix Security 2023). 
The APHP tool harnesses the power of patches to detect API post-handling bugs. It encapsulates two key modules: the APH Specification Extraction and the Bug Detection.
The APH Specification Extraction module examines patches to extract APH specifications. These specifications are then leveraged by the Bug Detection module to identify potential bugs and generate corresponding reports.

This artifact primarily focuses on the extraction of paired function call types of APH specifications, which is able to extract valuable specifications from patches and identifying numerous bugs.
Additionally, this artifact includes scripts for gathering the input patches consumed by APHP.

For more details, please refer to [our paper](./paper/sec23fall-final585.pdf).

## Structure

| Directory/File      | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `APHPatchCollect`   | Source code to collect APH patches. Also provides the patches we collected in APH-patch-dataset directory. |
| `APHP-src`          | The core of APHP. |
| ├─ `BugDetection`   | The bug detection module. |
| ├─ `config`         | Configuration for running APHP. |
| ├─ `SpecificationExtraction` | The specification extract module. |
| └─ `utils`          | Utility scripts. |
| `data`              | Directory to save output data, and sample data for testing. |
| `INSTALL.md`        | Instructions on how to install and set up.                      |
| `scripts`           | Useful scripts for automated testing and for facilitating manual verification. |
| `tools`             | Files related to third-party tools that are used in this project. |



## Installation
For installation, Please see [installation instructions](./INSTALL.md) for more details.



## Usage

### Minimal running example

We provide a minimal running sample which uses a memory leak [patch e5548b05631e](https://github.com/torvalds/linux/commit/e5548b05631e) extract specification, suppose be tested on linux kernel v5.16-rc1, which checks a target API of dwc2_hcd_init. Run the command as follows:

```shell
./APHP-src/scripts/quick_test_for_one_patch.sh
```
The expected output should be the corresponding specification and report bug, you can diff the [expected output](./APHP-src/scripts/expected_output_for_quick_test) to check if everything is OK.



You can also refer to the script and test one target function for the given specification to check if the function violates.


### Batch Testing
We provide a [subset of APH patches](./data/sample_data/sample_patches_for_extracting.csv) for testing to facilitate specifications extraction and subsequent bug detection.

#### A. Specifications Extraction Testing

Run the following command:

```shell
./APHP-src/scripts/test_for_extract_specs.sh
```

**Execution time**: With 24-core CPUs setting, the script executed in about 34 seconds of wall-clock time, utilizing about 676.68 seconds of total CPU time.

**Specification Output**: The command line will output the extracted specification as well as a overview, you can also view these specifications in the `data/ExtractedSpecification/` directory.

#### B. Bug Detection Testing
Before testing, please make sure the tested programs are checkout to the branch you want to test.

- **Input specifications**: we provide slightly [refined specifications](./data/sample_data/sample_specs_for_detecting.csv) for bug detection. By focusing on specifications of error-prone APIs, numerous bugs can be discovered. 

Execute the following command:

```shell
./APHP-src/scripts/test_for_detect_bugs.sh
```

- **Execution time**: With 24-core CPUs setting, the script executed in about 21 minutes of wall-clock time, utilizing about 2.73 hours of total CPU time. Note that the time spent on bug detection varies greatly for each specification, specifically, if the target API has many callers, then the corresponding detection will be more time consuming.
- **On-demand testing**: you can also only test a given target API or a collection you want (the specification should be included in the specification ).


**Bug report output**
- **Bug reports**: After execution, you can find corresponding bug reports in the default report file (`data/BugReports/bug_report.csv`). We suggest validating a selection of these, especially those associated with error-prone specification APIs (such as `of_parse_phandle`). 
Note that bug_reports is updated as append every time, so it will save the previous records, which you can delete manually.

- **Intermediate data**: the detection phase generates some intermediate data in the `BugDetection/intermediate_data`, the file directory format is `{repo_name}/{target_API}`, you can see the target_API's callers informations, including their source code, CFG, ASG, etc., where source code is used to manually check whether the bug reports are true or not. Note that APHP inevitably generates false positives.




## Data for reference
We also provide some API pairs with the reference patches in file [API-pairs-with-patches.csv](./data/sample_data/API-pairs-with-patches.csv). You can evaluate them if you want.



## Additional Notes
- 1. **Validation of APHP.**
We have validated the feasibility and effectiveness of the APHP'idea. Limited by human resources, we haven't verified all of its results. Nonetheless, we believe it can discover more useful specifications and detect additional bugs beyond what we disclosed in our paper.

- 2. **Selective and Customized Specification Usage.**
For effective bug detection, we suggest a selective usage of specifications, considering possible errors in the specification extraction. These errors often related to APH patch collection issues or others. You can manually refine these specifications or create your own to address potential misidentifications by the tool.


- 3. **Path Conditions Collection.** The current implementation of Path Conditions Collection is simple and may not work well. In case of extraction failure, it defaults to stricter path conditions, such as set the API status (pre-condition) to `success` and path status (post-condition) to `error`. While these conditions are optional constraints, critical elements like target API, post-operation, and crucial variables are more essential to functionality and don't have default values.

- 4. **Multiprocessing for Speed.** APHP leverages multiprocessing for rapid analysis, significantly accelerating time-intensive processes like Joern. Weggli also supports multiprocessing for efficient pattern matching in large projects. You can customize the CPU usage by modifying the `CPU_COUNT` setting in the `config.py` in [specification extraction](./APHP-src/SpecificationExtraction/config.py) and [bug detection](./APHP-src/BugDetection/config.py) , the default value is `24`


## About

This project is authored and maintained by Miaoqian Lin. For any problems, you can submit an issue to the GitHub repository.