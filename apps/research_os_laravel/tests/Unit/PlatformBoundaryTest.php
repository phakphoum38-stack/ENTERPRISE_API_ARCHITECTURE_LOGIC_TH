<?php

declare(strict_types=1);

namespace Tests\Unit;

use ResearchOS\Platform\Contracts\AuthorizationDecision;
use ResearchOS\Platform\Contracts\AuthorizationGateway;
use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Infrastructure\NullAuthorizationGateway;
use PHPUnit\Framework\TestCase;

final class PlatformBoundaryTest extends TestCase
{
    public function testAuthorizationFailsClosedWithoutCanonicalAdapter(): void
    {
        $gateway = new NullAuthorizationGateway();
        $decision = $gateway->decide(
            new RequestContext('req-1', 'corr-1', 'system', '1.0.0'),
            'workflow.execute',
            'workflow:test',
        );

        self::assertSame(AuthorizationDecision::UNKNOWN, $decision);
        self::assertInstanceOf(AuthorizationGateway::class, $gateway);
    }
}
