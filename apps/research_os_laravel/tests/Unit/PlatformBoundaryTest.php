<?php

declare(strict_types=1);

use ResearchOS\Platform\Contracts\AuthorizationDecision;
use ResearchOS\Platform\Contracts\AuthorizationGateway;
use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Infrastructure\NullAuthorizationGateway;

it('fails closed when no canonical authorization adapter is configured', function (): void {
    $gateway = new NullAuthorizationGateway();
    $decision = $gateway->decide(
        new RequestContext('req-1', 'corr-1', 'system', '1.0.0'),
        'workflow.execute',
        'workflow:test',
    );

    expect($decision)->toBe(AuthorizationDecision::UNKNOWN);
    expect($gateway)->toBeInstanceOf(AuthorizationGateway::class);
});
