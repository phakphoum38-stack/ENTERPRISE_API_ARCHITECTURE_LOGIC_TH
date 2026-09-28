<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Application;
use ResearchOS\Platform\Contracts\OperationsGateway;
final class OperationsApplicationService {
    public function __construct(private readonly OperationsGateway $gateway) {}
    public function snapshot(): array { return $this->gateway->snapshot(); }
}
