<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Application;
use ResearchOS\Platform\Contracts\ControlGateway;
use ResearchOS\Platform\Contracts\RequestContext;
final class ControlApplicationService {
    public function __construct(private readonly ControlGateway $gateway) {}
    public function execute(RequestContext $context, array $command): array {
        return $this->gateway->execute($context, $command);
    }
}
