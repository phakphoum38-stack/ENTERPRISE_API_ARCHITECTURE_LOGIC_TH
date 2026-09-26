<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

enum AuthorizationDecision: string
{
    case ALLOWED = 'ALLOWED';
    case DENIED = 'DENIED';
    case UNKNOWN = 'UNKNOWN';
}
