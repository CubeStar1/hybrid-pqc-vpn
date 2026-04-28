---
publisher: "ietf.org"
lang: "en"
author: "Kris Kwiatkowski"
title: "Post-quantum hybrid ECDHE-MLKEM Key Agreement for TLSv1.3"
description: "This draft defines two hybrid key agreements for TLS 1.3: X25519MLKEM768 and SecP256r1MLKEM768, which combine
a post-quantum KEM with an elliptic curve Diffie-Hellman (ECDHE)."
url: "https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html"
date: "2024-09-10T05:27:08.000Z"
word_count: 1653
reading_time: "7 min read"
---

## Table of Contents

- [Abstract](#abstract)
- [About This Document](#about-this-document)
- [Status of This Memo](#status-of-this-memo)
- [1. Introduction](#1-introduction)
  - [1.1. Motivation](#11-motivation)
- [2. Conventions and Definitions](#2-conventions-and-definitions)
- [3. Negotiated Groups](#3-negotiated-groups)
  - [3.1. Construction](#31-construction)
- [4. Security Considerations](#4-security-considerations)
- [5. IANA Considerations](#5-iana-considerations)
  - [5.3. Obsoleted Supported Groups](#53-obsoleted-supported-groups)
- [6. References](#6-references)
  - [6.1. Normative References](#61-normative-references)
  - [6.2. Informative References](#62-informative-references)
- [Appendix A. Change log](#appendix-a-change-log)

---

| Internet-Draft      | ECDHE-MLKEM           | September 2024 |
| ------------------- | --------------------- | -------------- |
| Kwiatkowski, et al. | Expires 14 March 2025 | \[Page\]       |

## Abstract

This draft defines two hybrid key agreements for TLS 1.3: X25519MLKEM768 and SecP256r1MLKEM768, which combine a post-quantum KEM with an elliptic curve Diffie-Hellman (ECDHE).[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-abstract-1)

## About This Document

This note is to be removed before publishing as an RFC.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-note.1-1)

The latest revision of this draft can be found at <https://post-quantum-cryptography.github.io/draft-kwiatkowski-tls-ecdhe-mlkem/>. Status information for this document may be found at <https://datatracker.ietf.org/doc/draft-kwiatkowski-tls-ecdhe-mlkem/>.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-note.1-2)

Discussion of this document takes place on the Transport Layer Security Working Group mailing list ([mailto:tls@ietf.org](mailto:tls@ietf.org)), which is archived at <https://mailarchive.ietf.org/arch/browse/tls/>. Subscribe at <https://www.ietf.org/mailman/listinfo/tls/>.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-note.1-3)

Source for this draft and an issue tracker can be found at <https://github.com/post-quantum-cryptography/draft-kwiatkowski-tls-ecdhe-mlkem>.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-note.1-4)

## Status of This Memo

This Internet-Draft is submitted in full conformance with the provisions of BCP 78 and BCP 79.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-boilerplate.1-1)

Internet-Drafts are working documents of the Internet Engineering Task Force (IETF). Note that other groups may also distribute working documents as Internet-Drafts. The list of current Internet-Drafts is at <https://datatracker.ietf.org/drafts/current/>.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-boilerplate.1-2)

Internet-Drafts are draft documents valid for a maximum of six months and may be updated, replaced, or obsoleted by other documents at any time. It is inappropriate to use Internet-Drafts as reference material or to cite them other than as "work in progress." [¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-boilerplate.1-3)

This Internet-Draft will expire on 14 March 2025.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-boilerplate.1-4)

## 1. Introduction

### 1.1. Motivation

ML-KEM is a key encapsulation method (KEM) defined in the \[[FIPS203](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#FIPS203)\]. It is designed to withstand cryptanalytic attacks from quantum computers.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-1.1-1)

This document introduces two new supported groups for hybrid post-quantum key agreements in TLS 1.3: X25519MLKEM768 and SecP256r1MLKEM768. Both combine ML-KEM-768 with ECDH in the manner of \[[hybrid](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#hybrid)\].[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-1.1-2)

The first one uses X25519 \[[rfc7748](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#rfc7748)\] and is an update to X25519Kyber768Draft00 \[[xyber](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#xyber)\], the most widely deployed PQ/T hybrid combiner for TLS v1.3 deployed in 2024.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-1.1-3)

The second one uses secp256r1 (NIST P-256) \[[ECDSA](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#ECDSA)\] \[[DSS](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#DSS)\]. The goal of this group is to support a use case that requires both shared secrets to be generated by FIPS-approved mechanisms.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-1.1-4)

Both constructions aim to provide a FIPS-approved key-establishment scheme (as per \[[SP56C](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#SP56C)\]).[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-1.1-5)

## 2. Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 \[[RFC2119](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#RFC2119)\] \[[RFC8174](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#RFC8174)\] when, and only when, they appear in all capitals, as shown here.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-2-1)

## 3. Negotiated Groups

Both groups enable the derivation of TLS session keys using FIPS-approved schemes. NIST's special publication 800-56Cr2 \[[SP56C](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#SP56C)\] approves the usage of HKDF \[[HKDF](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#HKDF)\] with two distinct shared secrets, with the condition that the first one is computed by a FIPS-approved key-establishment scheme. FIPS also requires a certified implementation of the scheme, which will remain more ubiqutous for secp256r1 in the coming years.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-3-1)

For this reason we put the ML-KEM-768 shared secret first in X25519MLKEM768, and the secp256r1 shared secret first in SecP256r1MLKEM768.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-3-2)

### 3.1. Construction

## 4. Security Considerations

The same security considerations as those described in \[[hybrid](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#hybrid)\] apply to the approach used by this document. The security analysis relies crucially on the TLS 1.3 message transcript, and one cannot assume a similar hybridisation is secure in other protocols.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-4-1)

Implementers are encouraged to use implementations resistant to side-channel attacks, especially those that can be applied by remote attackers.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-4-2)

## 5. IANA Considerations

This document requests/registers two new entries to the TLS Supported Groups registry, according to the procedures in [Section 6](https://datatracker.ietf.org/doc/html/draft-ietf-tls-rfc8447bis-09#section-6) of \[[tlsiana](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#tlsiana)\]. These identifiers are to be used with the final, ratified by NIST, version of ML-KEM which is specified in \[[FIPS203](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#FIPS203)\].[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-5-1)

### 5.3. Obsoleted Supported Groups

This document obsoletes 25497 and 25498 in the TLS Supported Groups registry.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#section-5.3-1)

## 6. References

### 6.1. Normative References

\[FIPS203\]
"Module-Lattice-Based Key-Encapsulation Mechanism Standard", National Institute of Standards and Technology, DOI 10.6028/nist.fips.203, August 2024, \< <https://doi.org/10.6028/nist.fips.203> \>.

\[RFC2119\]
Bradner, S., "Key words for use in RFCs to Indicate Requirement Levels", BCP 14, RFC 2119, DOI 10.17487/RFC2119, March 1997, \< <https://www.rfc-editor.org/rfc/rfc2119> \>.

\[rfc7748\]
Langley, A., Hamburg, M., and S. Turner, "Elliptic Curves for Security", RFC 7748, DOI 10.17487/RFC7748, January 2016, \< <https://www.rfc-editor.org/rfc/rfc7748> \>.

\[RFC8174\]
Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words", BCP 14, RFC 8174, DOI 10.17487/RFC8174, May 2017, \< <https://www.rfc-editor.org/rfc/rfc8174> \>.

\[RFC8446\]
Rescorla, E., "The Transport Layer Security (TLS) Protocol Version 1.3", RFC 8446, DOI 10.17487/RFC8446, August 2018, \< <https://www.rfc-editor.org/rfc/rfc8446> \>.

\[SP56C\]
Barker, E., Chen, L., and R. Davis, "Recommendation for Key-Derivation Methods in Key-Establishment Schemes", National Institute of Standards and Technology, DOI 10.6028/nist.sp.800-56cr2, August 2020, \< <https://doi.org/10.6028/nist.sp.800-56cr2> \>.

### 6.2. Informative References

\[DSS\]
Chen, L., Moody, D., Regenscheid, A., Robinson, A., and K. Randall, "Recommendations for Discrete Logarithm-based Cryptography:: Elliptic Curve Domain Parameters", National Institute of Standards and Technology, DOI 10.6028/nist.sp.800-186, February 2023, \< <https://doi.org/10.6028/nist.sp.800-186> \>.

\[ECDSA\]
American National Standards Institute, "Public Key Cryptography for the Financial Services Industry: The Elliptic Curve Digital Signature Algorithm (ECDSA)", ANSI ANS X9.62-2005, November 2005.

\[HKDF\]
Krawczyk, H. and P. Eronen, "HMAC-based Extract-and-Expand Key Derivation Function (HKDF)", RFC Editor, DOI 10.17487/rfc5869, May 2010, \< <https://doi.org/10.17487/rfc5869> \>.

\[hybrid\]
Stebila, D., Fluhrer, S., and S. Gueron, "Hybrid key exchange in TLS 1.3", Work in Progress, Internet-Draft, draft-ietf-tls-hybrid-design-10, 5 April 2024, \< <https://datatracker.ietf.org/doc/html/draft-ietf-tls-hybrid-design-10> \>.

\[tlsiana\]
Salowey, J. A. and S. Turner, "IANA Registry Updates for TLS and DTLS", Work in Progress, Internet-Draft, draft-ietf-tls-rfc8447bis-09, 30 April 2024, \< <https://datatracker.ietf.org/doc/html/draft-ietf-tls-rfc8447bis-09> \>.

\[xyber\]
Westerbaan, B. and D. Stebila, "X25519Kyber768Draft00 hybrid post-quantum key agreement", Work in Progress, Internet-Draft, draft-tls-westerbaan-xyber768d00-03, 24 September 2023, \< <https://datatracker.ietf.org/doc/html/draft-tls-westerbaan-xyber768d00-03> \>.

## Appendix A. Change log

- draft-kwiatkowski-tls-ecdhe-mlkem-02:[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.1.1)

  - Adds section that mentions supported groups that this document obsoletes.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.1.2.1.1)

  - Fix a reference to encapsulation in the FIPS 203.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.1.2.2.1)

- draft-kwiatkowski-tls-ecdhe-mlkem-01:[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.2.1)

  - Add X25519MLKEM768 [¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.2.2.1.1)

- draft-kwiatkowski-tls-ecdhe-mlkem-00:[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.3.1)

  - Change Kyber name to ML-KEM [¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.3.2.1.1)

  - Swap reference to I-D.cfrg-schwabe-kyber with FIPS-203 [¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.3.2.2.1)

  - Change codepoint. New value is equal to old value + 1.[¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.3.2.3.1)

- draft-kwiatkowski-tls-ecdhe-kyber-01: Fix size of key shares generated by the client and the server [¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.4.1)

- draft-kwiatkowski-tls-ecdhe-kyber-00: updates following IANA review [¶](https://www.ietf.org/archive/id/draft-kwiatkowski-tls-ecdhe-mlkem-02.html#appendix-A-1.5.1)