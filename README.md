# Second Look

A local-first "before you reply" checker for freelancers and side hustlers.

Paste a client message, job post, or payment email. Second Look flags the classic side-hustle payment traps (an invoice sent *to you*, "pay for the training kit first", overpay-and-refund, moving off-platform before escrow, gift cards, pressure to hurry) and drafts a calm reply that keeps money on-platform. Nothing leaves your laptop.

- **Plain-code rules decide the verdict** (Looks OK / Be careful / Stop), each with the exact words that triggered it.
- **A small open-weight model running locally** (Gemma 3 1B, via llama.cpp) only explains the result and drafts the reply. It can't change the verdict, and a guard rejects any draft that tells you to pay, click, or share personal info.

Status: work in progress, built for the DEV Hacktoberfest Open-Source AI Challenge, Week 2 ("Side Hustle"). Project started Oct 12, 2026.

Built with AI coding assistance.

License: MIT
