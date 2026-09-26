<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface AuthorizationGateway
{
    public function decide(RequestContext $context, string $capability, string $resource): AuthorizationDecision;
}
