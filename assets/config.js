/*
 * config.js: settings you can change without touching any other code.
 *
 * Loaded before questions.js and survey.js. Plain script (not an ES module) so the
 * page also works when index.html is opened straight from disk.
 */
window.DHAR_CONFIG = {

  /*
   * WHERE ANSWERS GO
   * The address is stored in two halves and joined at run time. That keeps the full
   * address out of the page source as plain text, which is a light deterrent against
   * simple scrapers. It is NOT secret: it appears in the email the respondent sends.
   * To change the inbox, change both halves.
   */
  recipientUser: 'garbaabdullahi344',
  recipientDomain: 'gmail.com',

  /* Prefix of the email subject. The page appends the respondent's role(s). */
  subjectPrefix: 'Shaping Dhar survey response',

  /*
   * EMAIL LENGTH LIMITS (characters in the final, percent-encoded link)
   *
   * A mailto: link carries the whole message inside the URL, and some email apps
   * cut or reject long ones (classic Outlook on Windows is the known strict case).
   * The page tries three forms, in this order, and uses the first that fits:
   *
   *   1. full     every question's full wording, then the answer
   *   2. compact  the same answers, with long question wording shortened
   *               ("Question wording: shortened" is printed in the header)
   *   3. cut      the compact text, cut at a line break and marked as cut. The
   *               report is written contact first, then basics and sentiment, so
   *               a cut loses the least important part.
   *
   * In every case the complete answers are copied to the clipboard, and the
   * respondent can use "Copy answers" or "Download .txt" on the confirmation panel.
   *
   * These numbers are cautious guesses, NOT measured limits. Raise them if you
   * find that your readers' email apps accept more.
   *
   *   mailtoLimitWindows : mailto: links on Windows (kept conservative)
   *   mailtoLimitOther   : mailto: links on Android, iOS, macOS, Linux
   *   webComposeLimit    : Gmail / Outlook / Yahoo "compose in the browser" links
   */
  mailtoLimitWindows: 1900,
  mailtoLimitOther: 7500,
  webComposeLimit: 7000,

  /*
   * PDF COPY OF THE RESPONSE
   * On the review step the page makes a PDF of the questions and the respondent's answers,
   * entirely on their device. Pressing Send saves it and opens the email draft; the
   * respondent attaches it. (A web page cannot attach a file to an email by itself.)
   * The draft always carries the answers as text too, so nothing depends on the attachment.
   *
   *   pdfEnabled      : false removes the PDF step and goes back to a text-only email
   *   pdfAutoDownload : false makes the PDF a button on the confirmation panel instead of
   *                     saving it as soon as Send is pressed
   */
  pdfEnabled: true,
  pdfAutoDownload: true,

  /* Browser storage key prefix for unfinished answers (kept on the device only). */
  storagePrefix: 'dhar-survey',

  /* Shown in the page footer. Leave repoUrl empty to hide the link. */
  repoUrl: 'https://github.com/garba-the-analyst/forge-of-dhar/tree/gh-pages',
  licenseNote: 'Open source under the MIT licence'
};
