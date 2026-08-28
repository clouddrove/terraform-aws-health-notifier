# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.0.1] - 2026-08-28
### :sparkles: New Features
- [`bb6e6ef`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/bb6e6efd7f8bacd9c75ddabce51455a4ff6b43d2) - route AWS Health events to a pluggable notifier, with Jira as the first backend *(PR [#1](https://github.com/clouddrove/terraform-aws-health-notifier/pull/1) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`eebedb7`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/eebedb7e6bb426fb66df8e0cbe9f6b70defdbcf3) - add a GitHub Issues notifier and notifier selection *(PR [#6](https://github.com/clouddrove/terraform-aws-health-notifier/pull/6) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`6ad0e0c`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/6ad0e0c3d68288d04155cc1ca87b1429ad2b0731) - fan out a single AWS Health event to multiple notifiers *(PR [#7](https://github.com/clouddrove/terraform-aws-health-notifier/pull/7) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`d0a0bba`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/d0a0bba484c6eed72e74d518ac0cb5f5836d173c) - add opt-in EC2 instance tag enrichment *(PR [#8](https://github.com/clouddrove/terraform-aws-health-notifier/pull/8) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`331bb24`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/331bb243360a9a3a61e1bd875ac7c534a8bf6da6) - add Linear as a third notifier *(PR [#20](https://github.com/clouddrove/terraform-aws-health-notifier/pull/20) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`721182a`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/721182a3212dae361edd821b8ccb8208bb154a25) - add a Slack notifier *(PR [#28](https://github.com/clouddrove/terraform-aws-health-notifier/pull/28) by [@clouddrove-ci](https://github.com/clouddrove-ci))*

### :bug: Bug Fixes
- [`8cea378`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/8cea378febe7a77786ccbc0c52cc1c4c587f3f10) - stop shadowing genie's readme target *(PR [#30](https://github.com/clouddrove/terraform-aws-health-notifier/pull/30) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`ac6c187`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/ac6c18773f536e7e1f488b3dd3476ae73451e123) - repair the changelog workflow so releases actually generate one *(PR [#32](https://github.com/clouddrove/terraform-aws-health-notifier/pull/32) by [@clouddrove-ci](https://github.com/clouddrove-ci))*

### :recycle: Refactors
- [`6acfdf9`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/6acfdf92289a4663b807576f955b7542e304771e) - rebuild as a CloudDrove module repo *(PR [#25](https://github.com/clouddrove/terraform-aws-health-notifier/pull/25) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`e987c6e`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/e987c6e749e9d4f9c1edf2a88eaa9a84e2a14a7e) - drop the deploy root; this is a module, not a deployment *(PR [#26](https://github.com/clouddrove/terraform-aws-health-notifier/pull/26) by [@clouddrove-ci](https://github.com/clouddrove-ci))*

### :memo: Documentation Changes
- [`5ddabe1`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/5ddabe1321acafef05f4c936fa37c63d13a217f8) - move the README source of truth into README.yaml *(PR [#29](https://github.com/clouddrove/terraform-aws-health-notifier/pull/29) by [@clouddrove-ci](https://github.com/clouddrove-ci))*

### :construction_worker: CI
- [`4d6b368`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/4d6b368e2f1a1c52fa103c72a2591ab3c07bc958) - make deploy manual-only via workflow_dispatch *(PR [#5](https://github.com/clouddrove/terraform-aws-health-notifier/pull/5) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`d083fb3`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/d083fb30523f15315f4cfa1c6e87aebc30f736c3) - run the readme workflow manually until the GITHUB secret exists *(PR [#31](https://github.com/clouddrove/terraform-aws-health-notifier/pull/31) by [@clouddrove-ci](https://github.com/clouddrove-ci))*

### :wrench: Chores
- [`7cd872a`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/7cd872a021b49cdb48b8874c5df84d81d8117733) - enable Dependabot and remove design docs *(PR [#2](https://github.com/clouddrove/terraform-aws-health-notifier/pull/2) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`14b6093`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/14b6093eaadb10d4c07f7aa2a37d70fec96fd584) - bump python from 3.13-slim to 3.14-slim *(PR [#3](https://github.com/clouddrove/terraform-aws-health-notifier/pull/3) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`1662cc9`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/1662cc94b3a0758deb53a9b7de032265bd5e0e99) - bump the actions group with 5 updates *(PR [#4](https://github.com/clouddrove/terraform-aws-health-notifier/pull/4) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`edb2718`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/edb271888358a7ddda539954d8dc2dad8d1c6f7c) - bump hashicorp/aws in /terraform in the terraform group *(PR [#9](https://github.com/clouddrove/terraform-aws-health-notifier/pull/9) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`0b66c0e`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/0b66c0e99dabeaca428df05b259d5f482bf43a15) - bump bridgecrewio/checkov-action in the actions group *(PR [#10](https://github.com/clouddrove/terraform-aws-health-notifier/pull/10) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`bce52d4`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/bce52d455bc359813e101c91573a962de1069e5a) - bump bridgecrewio/checkov-action in the actions group *(PR [#11](https://github.com/clouddrove/terraform-aws-health-notifier/pull/11) by [@clouddrove-ci](https://github.com/clouddrove-ci))*
- [`0f90cde`](https://github.com/clouddrove/terraform-aws-health-notifier/commit/0f90cde741b484c17e9dd3bd84cd53e0838becb6) - bump hashicorp/aws in /terraform in the terraform group *(PR [#12](https://github.com/clouddrove/terraform-aws-health-notifier/pull/12) by [@clouddrove-ci](https://github.com/clouddrove-ci))*

