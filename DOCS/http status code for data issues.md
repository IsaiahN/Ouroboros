# useful compression table for model explaining issues that i can verifiably look up.

100 Continue
101 Switching Protocols
102 Processing (WebDAV; RFC 2518)
103 Early Hints (RFC 8297)
1xx informational response
200 OK
201 Created
202 Accepted
203 Non-Authoritative Information (since HTTP/1.1)
204 No Content
205 Reset Content
206 Partial Content
207 Multi-Status (WebDAV; RFC 4918)
208 Already Reported (WebDAV; RFC 5842)
218 This is fine
226 IM Used (RFC 3229)
2xx success
300 Multiple Choices
301 Moved Permanently
302 Found
303 See Other (since HTTP/1.1)
304 Not Modified
305 Use Proxy (since HTTP/1.1)
306 Switch Proxy
307 Temporary Redirect (since HTTP/1.1)
308 Permanent Redirect
3xx redirection
400 Bad Request
401 Unauthorized
402 Payment Required
403 Forbidden
404 Not Found
404 error on Wikimedia
405 Method Not Allowed
406 Not Acceptable
407 Proxy Authentication Required
408 Request Timeout
409 Conflict
410 Gone
411 Length Required
412 Precondition Failed
413 Payload Too Large
414 URI Too Long
415 Unsupported Media Type
416 Range Not Satisfiable
417 Expectation Failed
418 I'm a teapot (RFC 2324, RFC 7168)
419 Page Expired
420 Enhance Your Calm
420 Method Failure
421 Misdirected Request
422 Unprocessable Content
423 Locked (WebDAV; RFC 4918)
424 Failed Dependency (WebDAV; RFC 4918)
425 Too Early (RFC 8470)
426 Upgrade Required
428 Precondition Required (RFC 6585)
429 Too Many Requests (RFC 6585)
430 Request Header Fields Too Large
430 Shopify Security Rejection
431 Request Header Fields Too Large (RFC 6585)
440 Login Time-out
444 No Response
449 Retry With
450 Blocked by Windows Parental Controls
451 Redirect
451 Unavailable For Legal Reasons (RFC 7725)
494 Request header too large
495 SSL Certificate Error
496 SSL Certificate Required
497 HTTP Request Sent to HTTPS Port
498 Invalid Token
499 Client Closed Request
499 Token Required
4xx client error
500 Internal Server Error
501 Not Implemented
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
505 HTTP Version Not Supported
506 Variant Also Negotiates (RFC 2295)
507 Insufficient Storage (WebDAV; RFC 4918)
508 Loop Detected (WebDAV; RFC 5842)
508 Resource Limit Is Reached
509 Bandwidth Limit Exceeded
510 Not Extended (RFC 2774)
511 Network Authentication Required (RFC 6585)
520 Web Server Returned an Unknown Error
521 Web Server Is Down
522 Connection Timed Out
523 Origin Is Unreachable
524 A Timeout Occurred
525 SSL Handshake Failed
526 Invalid SSL Certificate
527 Railgun Error (obsolete)
529 Site is overloaded
530 Origin DNS Error
530 Origin Unavailable
530 Site is frozen
540 Temporarily Disabled
561 Unauthorized
598 Network read timeout error
599 Network Connect Timeout Error
5xx server error
5xx status indicates that the server is aware that it has encountered an error or is otherwise incapable of performing the request. Except when responding to a HEAD request, the server should include an entity containing an explanation of the error situation, and indicate whether it is a temporary or permanent condition. Likewise, user agents should display any included entity to the user. These response codes are applicable to any request method.
783 Unexpected Token
999 Request denied