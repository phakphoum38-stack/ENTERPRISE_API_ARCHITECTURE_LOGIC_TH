<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface IdentityGateway
{
    public function resolve(RequestContext $context): string;
}
