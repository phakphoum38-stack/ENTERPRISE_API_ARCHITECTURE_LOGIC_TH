<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\AuthorizationDecision;
use ResearchOS\Platform\Contracts\AuthorizationGateway;
use ResearchOS\Platform\Contracts\RequestContext;

final class NullAuthorizationGateway implements AuthorizationGateway
{
    public function decide(RequestContext $context, string $capability, string $resource): AuthorizationDecision
    {
        return AuthorizationDecision::UNKNOWN;
    }
}
